import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
from pathlib import Path
import yaml


class DebugTracker:
    """
    Comprehensive debug tracking system for shopping pipeline
    Creates separate folder per query with all decision artifacts
    """
    
    def __init__(self, query: str, debug_base_dir: str = "debug"):
        self.query = query
        self.start_time = time.time()
        
        # Create unique folder name based on query and timestamp
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"{timestamp}_{query_hash}"
        
        # Create debug directory structure
        self.debug_dir = Path(debug_base_dir) / self.session_id
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tracking data organized by domain
        self.data = {
            "session_metadata": {
                "query": query,
                "session_id": self.session_id,
                "start_time": self.start_time,
                "start_timestamp": datetime.now().isoformat(),
                "total_duration": 0,
                "summary": {
                    "total_domains_searched": 0,
                    "total_raw_products": 0,
                    "total_prefiltered": 0,
                    "total_final": 0,
                    "overall_conversion_rate": "0.0%"
                }
            },
            "domains": {},  # Will be populated per domain
            "search_results": {
                "sources": [],
                "total_found": 0,
                "timing": {}
            },
            "llm_decisions": {
                "products_selected": [],
                "selection_criteria": [],
                "rejected_products": []
            },
            "url_validation": {
                "invalid_links": [],
                "invalid_domains": [],
                "validation_errors": []
            },
            "timing": {
                "phases": {},
                "total_duration": 0
            },
            "errors": [],
            "final_results": {
                "products_shown": 0,
                "links_shown": 0
            }
        }
        
        # Save initial session info
        self.save_session_info()
    
    def track_shopify_json(self, raw_data: List[Dict], prefiltered: List[Dict], filtered: List[Dict], domain: str = "unknown"):
        """Track Shopify JSON data at each filtering stage organized by domain"""
        
        # Initialize domain data if not exists
        if domain not in self.data["domains"]:
            self.data["domains"][domain] = {
                "raw_products": {
                    "count": 0,
                    "sample_products": []
                },
                "prefiltered": {
                    "count": 0,
                    "products": [],
                    "decisions": []
                },
                "filtered": {
                    "count": 0,
                    "products": [],
                    "decisions": []
                },
                "conversion_rates": {
                    "raw_to_prefiltered": "0.0%",
                    "prefiltered_to_filtered": "0.0%",
                    "overall": "0.0%"
                },
                "timing": {}
            }
        
        domain_data = self.data["domains"][domain]
        
        # Update domain-specific data
        domain_data["raw_products"]["count"] = len(raw_data)
        domain_data["prefiltered"]["count"] = len(prefiltered)
        domain_data["filtered"]["count"] = len(filtered)
        
        # Calculate conversion rates for this domain
        if len(raw_data) > 0:
            prefilter_rate = len(prefiltered) / len(raw_data) * 100
            domain_data["conversion_rates"]["raw_to_prefiltered"] = f"{prefilter_rate:.1f}%"
            
            if len(prefiltered) > 0:
                filter_rate = len(filtered) / len(prefiltered) * 100
                domain_data["conversion_rates"]["prefiltered_to_filtered"] = f"{filter_rate:.1f}%"
            
            overall_rate = len(filtered) / len(raw_data) * 100
            domain_data["conversion_rates"]["overall"] = f"{overall_rate:.1f}%"
        
        # Store sample raw products for this domain
        domain_data["raw_products"]["sample_products"] = [
            {
                "title": p.get("title", "Unknown"),
                "product_type": p.get("product_type", ""),
                "vendor": p.get("vendor", ""),
                "price": p.get("variants", [{}])[0].get("price", "0") if p.get("variants") else "0",
                "handle": p.get("handle", "")
            }
            for p in raw_data[:5]  # First 5 products per domain
        ]
        
        # Store prefiltered and filtered products
        domain_data["prefiltered"]["products"] = prefiltered[:10]  # Top 10 per domain
        domain_data["filtered"]["products"] = filtered[:10]  # Top 10 per domain
        
        # Update session summary
        self.data["session_metadata"]["summary"]["total_domains_searched"] = len(self.data["domains"])
        self.data["session_metadata"]["summary"]["total_raw_products"] += len(raw_data)
        self.data["session_metadata"]["summary"]["total_prefiltered"] += len(prefiltered)
        self.data["session_metadata"]["summary"]["total_final"] += len(filtered)
        
        # Save updated session data (all domains in one file)
        self.save_session_info()
        
        print(f"🐛 DEBUG: Saved Shopify data for {domain} - Raw: {len(raw_data)}, Prefiltered: {len(prefiltered)}, Filtered: {len(filtered)}")
    
    def track_prefilter_decision(self, product: Dict, reason: str, action: str, domain: str = "unknown"):
        """Track prefiltering decisions (keep/remove) by domain"""
        # Initialize domain if not exists
        if domain not in self.data["domains"]:
            self.data["domains"][domain] = {
                "raw_products": {"count": 0, "sample_products": []},
                "prefiltered": {"count": 0, "products": [], "decisions": []},
                "filtered": {"count": 0, "products": [], "decisions": []},
                "conversion_rates": {"raw_to_prefiltered": "0.0%", "prefiltered_to_filtered": "0.0%", "overall": "0.0%"},
                "timing": {}
            }
        
        decision = {
            "product_name": product.get("title", "Unknown"),
            "reason": reason,
            "action": action,  # "kept" or "removed"
            "price": product.get("variants", [{}])[0].get("price", "Unknown"),
            "timestamp": time.time() - self.start_time
        }
        self.data["domains"][domain]["prefiltered"]["decisions"].append(decision)
    
    def track_filter_decision(self, product: Dict, reason: str, action: str, domain: str = "unknown"):
        """Track main filtering decisions by domain"""
        # Initialize domain if not exists
        if domain not in self.data["domains"]:
            self.data["domains"][domain] = {
                "raw_products": {"count": 0, "sample_products": []},
                "prefiltered": {"count": 0, "products": [], "decisions": []},
                "filtered": {"count": 0, "products": [], "decisions": []},
                "conversion_rates": {"raw_to_prefiltered": "0.0%", "prefiltered_to_filtered": "0.0%", "overall": "0.0%"},
                "timing": {}
            }
        
        decision = {
            "product_name": product.get("product_name", "Unknown"),
            "reason": reason,
            "action": action,
            "price": product.get("price", "Unknown"),
            "timestamp": time.time() - self.start_time
        }
        self.data["domains"][domain]["filtered"]["decisions"].append(decision)
    
    def track_llm_selection(self, selected_products: List[Dict], criteria: List[str], rejected: List[Dict] = None):
        """Track LLM product selection decisions"""
        self.data["llm_decisions"]["products_selected"] = [
            {
                "name": p.get("name", p.get("product_name", "Unknown")),
                "price": p.get("price", "Unknown"),
                "store": p.get("store", "Unknown"),
                "reason": p.get("reasoning", "No reason provided")
            }
            for p in selected_products
        ]
        
        self.data["llm_decisions"]["selection_criteria"] = criteria
        
        if rejected:
            self.data["llm_decisions"]["rejected_products"] = [
                {
                    "name": p.get("name", p.get("product_name", "Unknown")),
                    "price": p.get("price", "Unknown"),
                    "rejection_reason": p.get("rejection_reason", "Not specified")
                }
                for p in rejected
            ]
        
        # Save detailed LLM decisions
        self.save_json("llm_selections.json", {
            "selected": selected_products,
            "criteria": criteria,
            "rejected": rejected or []
        })
        
        print(f"🐛 DEBUG: Tracked LLM selections - {len(selected_products)} selected, {len(rejected or [])} rejected")
    
    def track_invalid_url(self, url: str, reason: str, validation_type: str = "link"):
        """Track invalid URLs and domains"""
        invalid_entry = {
            "url": url,
            "reason": reason,
            "type": validation_type,  # "link" or "domain"
            "timestamp": time.time() - self.start_time
        }
        
        if validation_type == "domain":
            self.data["url_validation"]["invalid_domains"].append(invalid_entry)
        else:
            self.data["url_validation"]["invalid_links"].append(invalid_entry)
    
    def track_validation_error(self, url: str, error: str):
        """Track URL validation errors"""
        error_entry = {
            "url": url,
            "error": str(error),
            "timestamp": time.time() - self.start_time
        }
        self.data["url_validation"]["validation_errors"].append(error_entry)
    
    def start_timing_phase(self, phase_name: str):
        """Start timing a specific phase"""
        self.data["timing"]["phases"][phase_name] = {
            "start": time.time(),
            "end": None,
            "duration": None
        }
        print(f"🐛 DEBUG: Started timing phase: {phase_name}")
    
    def end_timing_phase(self, phase_name: str):
        """End timing a specific phase"""
        if phase_name in self.data["timing"]["phases"]:
            phase = self.data["timing"]["phases"][phase_name]
            phase["end"] = time.time()
            phase["duration"] = phase["end"] - phase["start"]
            print(f"🐛 DEBUG: Ended timing phase: {phase_name} ({phase['duration']:.3f}s)")
    
    def track_search_results(self, source: str, count: int, timing: float):
        """Track search results from different sources"""
        result = {
            "source": source,
            "count": count,
            "timing": timing,
            "timestamp": time.time() - self.start_time
        }
        self.data["search_results"]["sources"].append(result)
        self.data["search_results"]["total_found"] += count
        self.data["search_results"]["timing"][source] = timing
    
    def track_error(self, error: str, context: str = ""):
        """Track errors that occur during processing"""
        error_entry = {
            "error": str(error),
            "context": context,
            "timestamp": time.time() - self.start_time
        }
        self.data["errors"].append(error_entry)
        print(f"🐛 DEBUG: Tracked error in {context}: {error}")
    
    def finalize_session(self, products_shown: int = 0, links_shown: int = 0):
        """Finalize the debug session with final results"""
        self.data["timing"]["total_duration"] = time.time() - self.start_time
        self.data["final_results"]["products_shown"] = products_shown
        self.data["final_results"]["links_shown"] = links_shown
        self.data["end_timestamp"] = datetime.now().isoformat()
        
        # Save final session data
        self.save_session_info()
        
        # Create summary report
        self.create_summary_report()
        
        print(f"🐛 DEBUG: Session finalized - Duration: {self.data['timing']['total_duration']:.3f}s")
        print(f"🐛 DEBUG: Results saved to: {self.debug_dir}")
    
    def save_yaml(self, filename: str, data: Any):
        """Save data as YAML file"""
        filepath = self.debug_dir / filename
        try:
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
        except Exception as e:
            print(f"🐛 DEBUG: Error saving {filename}: {e}")
            # Continue execution - don't break main functionality for debug issues
    
    def save_json(self, filename: str, data: Any):
        """Save data as JSON file (legacy compatibility)"""
        filepath = self.debug_dir / filename
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"🐛 DEBUG: Error saving {filename}: {e}")
            # Continue execution - don't break main functionality for debug issues
    
    def save_session_info(self):
        """Save current session data"""
        # Calculate overall conversion rate
        total_raw = self.data["session_metadata"]["summary"]["total_raw_products"]
        total_final = self.data["session_metadata"]["summary"]["total_final"]
        if total_raw > 0:
            conversion_rate = (total_final / total_raw) * 100
            self.data["session_metadata"]["summary"]["overall_conversion_rate"] = f"{conversion_rate:.1f}%"
        
        # Save as YAML for better readability
        self.save_yaml("session_data.yaml", self.data)
        
        # Also save JSON for compatibility
        self.save_json("session_data.json", self.data)
    
    def create_summary_report(self):
        """Create a human-readable summary report"""
        # Get summary data
        summary_data = self.data['session_metadata']['summary']
        
        summary = f"""
DEBUG SUMMARY REPORT
===================

Query: {self.query}
Session ID: {self.session_id}
Total Duration: {self.data['timing']['total_duration']:.3f} seconds

SHOPIFY DATA PROCESSING:
- Total domains searched: {summary_data['total_domains_searched']}
- Raw JSON items: {summary_data['total_raw_products']}
- After prefiltering: {summary_data['total_prefiltered']}
- After main filtering: {summary_data['total_final']}
- Overall conversion rate: {summary_data['overall_conversion_rate']}

DOMAIN BREAKDOWN:
"""
        
        for domain, domain_data in self.data['domains'].items():
            summary += f"- {domain}: {domain_data['raw_products']['count']} → {domain_data['prefiltered']['count']} → {domain_data['filtered']['count']} products\n"
        
        summary += f"""

LLM DECISIONS:
- Products selected: {len(self.data['llm_decisions']['products_selected'])}
- Products rejected: {len(self.data['llm_decisions']['rejected_products'])}
- Selection criteria: {len(self.data['llm_decisions']['selection_criteria'])}

URL VALIDATION:
- Invalid links: {len(self.data['url_validation']['invalid_links'])}
- Invalid domains: {len(self.data['url_validation']['invalid_domains'])}
- Validation errors: {len(self.data['url_validation']['validation_errors'])}

TIMING BREAKDOWN:
"""
        
        for phase, timing in self.data['timing']['phases'].items():
            if timing.get('duration'):
                summary += f"- {phase}: {timing['duration']:.3f}s\n"
        
        summary += f"""
FINAL RESULTS:
- Products shown to user: {self.data['final_results']['products_shown']}
- Links shown to user: {self.data['final_results']['links_shown']}

ERRORS:
- Total errors: {len(self.data['errors'])}
"""
        
        if self.data['errors']:
            summary += "\nError Details:\n"
            for error in self.data['errors']:
                summary += f"- {error['context']}: {error['error']}\n"
        
        # Save summary report
        with open(self.debug_dir / "SUMMARY.txt", 'w') as f:
            f.write(summary)
        
        print(f"🐛 DEBUG: Summary report created")


# Global debug tracker instance
_debug_tracker: Optional[DebugTracker] = None

def init_debug_session(query: str) -> DebugTracker:
    """Initialize a new debug session or reuse existing one for the same query"""
    global _debug_tracker
    
    # Check if we already have an active session for the same query
    if _debug_tracker and _debug_tracker.query == query:
        print(f"🐛 DEBUG: Reusing existing session for query: '{query}'")
        print(f"🐛 DEBUG: Session folder: {_debug_tracker.debug_dir}")
        return _debug_tracker
    
    try:
        _debug_tracker = DebugTracker(query)
        print(f"🐛 DEBUG: Initialized NEW session for query: '{query}'")
        print(f"🐛 DEBUG: Session folder: {_debug_tracker.debug_dir}")
        return _debug_tracker
    except Exception as e:
        print(f"🐛 DEBUG: Failed to initialize debug session: {e}")
        _debug_tracker = None
        return _null_debug_tracker()

def get_debug_tracker() -> Optional[DebugTracker]:
    """Get the current debug tracker instance"""
    return _debug_tracker

def finalize_debug_session(products_shown: int = 0, links_shown: int = 0):
    """Finalize the current debug session"""
    global _debug_tracker
    if _debug_tracker:
        _debug_tracker.finalize_session(products_shown, links_shown)
        _debug_tracker = None


# Fallback function for when debug tracking is disabled
def _null_debug_tracker():
    """Returns None - used when debug tracking is not available"""
    return None 