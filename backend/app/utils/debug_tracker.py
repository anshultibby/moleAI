import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
from pathlib import Path


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
        
        # Initialize tracking data
        self.data = {
            "query": query,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "start_timestamp": datetime.now().isoformat(),
            "shopify_data": {
                "raw_json": None,
                "prefiltered_count": 0,
                "filtered_count": 0,
                "prefilter_reasons": [],
                "filter_reasons": []
            },
            "search_results": {
                "total_found": 0,
                "sources": [],
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
    
    def track_shopify_json(self, raw_data: List[Dict], prefiltered: List[Dict], filtered: List[Dict]):
        """Track Shopify JSON data at each filtering stage"""
        self.data["shopify_data"]["raw_json"] = len(raw_data)
        self.data["shopify_data"]["prefiltered_count"] = len(prefiltered)
        self.data["shopify_data"]["filtered_count"] = len(filtered)
        
        # Save raw data sample (first 10 items for review)
        sample_data = raw_data[:10] if raw_data else []
        self.save_json("shopify_raw_sample.json", sample_data)
        
        # Save full filtered data
        self.save_json("shopify_prefiltered.json", prefiltered)
        self.save_json("shopify_filtered.json", filtered)
        
        print(f"🐛 DEBUG: Saved Shopify data - Raw: {len(raw_data)}, Prefiltered: {len(prefiltered)}, Filtered: {len(filtered)}")
    
    def track_prefilter_decision(self, product: Dict, reason: str, action: str):
        """Track prefiltering decisions (keep/remove)"""
        decision = {
            "product_name": product.get("title", "Unknown"),
            "reason": reason,
            "action": action,  # "kept" or "removed"
            "price": product.get("variants", [{}])[0].get("price", "Unknown"),
            "timestamp": time.time() - self.start_time
        }
        self.data["shopify_data"]["prefilter_reasons"].append(decision)
    
    def track_filter_decision(self, product: Dict, reason: str, action: str):
        """Track main filtering decisions"""
        decision = {
            "product_name": product.get("product_name", "Unknown"),
            "reason": reason,
            "action": action,
            "price": product.get("price", "Unknown"),
            "timestamp": time.time() - self.start_time
        }
        self.data["shopify_data"]["filter_reasons"].append(decision)
    
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
    
    def save_json(self, filename: str, data: Any):
        """Save data as JSON file"""
        filepath = self.debug_dir / filename
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"🐛 DEBUG: Error saving {filename}: {e}")
            # Continue execution - don't break main functionality for debug issues
    
    def save_session_info(self):
        """Save current session data"""
        self.save_json("session_data.json", self.data)
    
    def create_summary_report(self):
        """Create a human-readable summary report"""
        summary = f"""
DEBUG SUMMARY REPORT
===================

Query: {self.query}
Session ID: {self.session_id}
Total Duration: {self.data['timing']['total_duration']:.3f} seconds

SHOPIFY DATA PROCESSING:
- Raw JSON items: {self.data['shopify_data']['raw_json'] or 'N/A'}
- After prefiltering: {self.data['shopify_data']['prefiltered_count']}
- After main filtering: {self.data['shopify_data']['filtered_count']}
- Prefilter decisions: {len(self.data['shopify_data']['prefilter_reasons'])}
- Filter decisions: {len(self.data['shopify_data']['filter_reasons'])}

SEARCH RESULTS:
- Total products found: {self.data['search_results']['total_found']}
- Sources used: {', '.join([s['source'] for s in self.data['search_results']['sources']])}

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
            if timing['duration']:
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
    """Initialize a new debug session"""
    global _debug_tracker
    try:
        _debug_tracker = DebugTracker(query)
        print(f"🐛 DEBUG: Initialized session for query: '{query}'")
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