"""
Funnel Visualizer for Shopify Product Filtering Pipeline
Creates detailed reports showing the entire filtering funnel
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml


class FunnelVisualizer:
    """
    Visualizes the complete Shopify product filtering funnel:
    Raw JSON → Prefiltered → LLM Filtered → Final Results
    """
    
    def __init__(self, query: str, output_dir: str = "funnel_reports"):
        self.query = query
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"{self.timestamp}_{hash(query) % 10000:04d}"
        
        # Create output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize funnel data organized by domain
        self.funnel_data = {
            "session_metadata": {
                "query": query,
                "session_id": self.session_id,
                "timestamp": self.timestamp,
                "total_duration": 0,
                "summary": {
                    "total_raw": 0,
                    "total_prefiltered": 0,
                    "total_llm_filtered": 0,
                    "total_final": 0,
                    "domains_searched": 0,
                    "conversion_rate": "0.0%"
                }
            },
            "domains": {},  # Will be populated per domain
            "stages": {
                "raw": {
                    "count": 0,
                    "products": [],
                    "sample_size": 20
                },
                "prefiltered": {
                    "count": 0,
                    "products": [],
                    "decisions": []
                },
                "llm_filtered": {
                    "count": 0,
                    "products": [],
                    "decisions": []
                },
                "final": {
                    "count": 0,
                    "products": []
                }
            },
            "stores_searched": [],
            "timing": {
                "stage_durations": {}
            },
            "global_decisions": {
                "prefilter_rejections": {},  # Reason -> count
                "llm_filter_rejections": {},  # Reason -> count
            },
            "errors": []
        }
        
        self.start_time = time.time()
        print(f"🔍 FUNNEL: Started tracking for query '{query}'")
    
    def track_raw_data(self, raw_products: List[Dict], store_domain: str):
        """Track raw Shopify JSON data"""
        stage = self.funnel_data["stages"]["raw"]
        stage["count"] += len(raw_products)
        
        # Add store to searched list
        if store_domain not in self.funnel_data["stores_searched"]:
            self.funnel_data["stores_searched"].append(store_domain)
        
        # Store sample of raw products for analysis
        sample_products = []
        for product in raw_products[:stage["sample_size"]]:
            sample_products.append({
                "title": product.get("title", "Unknown"),
                "product_type": product.get("product_type", ""),
                "vendor": product.get("vendor", ""),
                "tags": product.get("tags", [])[:5],  # First 5 tags
                "variants_count": len(product.get("variants", [])),
                "first_variant_price": product.get("variants", [{}])[0].get("price", "0") if product.get("variants") else "0",
                "handle": product.get("handle", ""),
                "store": store_domain
            })
        
        stage["products"].extend(sample_products)
        print(f"🔍 FUNNEL: Raw data - {len(raw_products)} products from {store_domain}")
    
    def track_prefilter_decision(self, product: Dict, reason: str, action: str):
        """Track individual prefiltering decisions"""
        decision = {
            "product_title": product.get("title", "Unknown"),
            "product_type": product.get("product_type", ""),
            "reason": reason,
            "action": action,  # "kept" or "removed"
            "price": product.get("variants", [{}])[0].get("price", "Unknown"),
            "tags": product.get("tags", [])[:3]  # First 3 tags for context
        }
        
        self.funnel_data["stages"]["prefiltered"]["decisions"].append(decision)
        
        if action == "kept":
            self.funnel_data["stages"]["prefiltered"]["count"] += 1
            # Store sample kept products
            if len(self.funnel_data["stages"]["prefiltered"]["products"]) < 20:
                self.funnel_data["stages"]["prefiltered"]["products"].append({
                    "title": product.get("title", "Unknown"),
                    "product_type": product.get("product_type", ""),
                    "price": product.get("variants", [{}])[0].get("price", "Unknown"),
                    "reason_kept": reason
                })
    
    def track_llm_filter_decision(self, product: Dict, reason: str, action: str):
        """Track LLM filtering decisions"""
        decision = {
            "product_name": product.get("product_name", "Unknown"),
            "price": product.get("price", "Unknown"),
            "store": product.get("store_name", "Unknown"),
            "reason": reason,
            "action": action,  # "kept" or "removed"
            "relevance_score": product.get("relevance_score", 0)
        }
        
        self.funnel_data["stages"]["llm_filtered"]["decisions"].append(decision)
        
        if action == "kept":
            self.funnel_data["stages"]["llm_filtered"]["count"] += 1
            # Store sample kept products
            if len(self.funnel_data["stages"]["llm_filtered"]["products"]) < 15:
                self.funnel_data["stages"]["llm_filtered"]["products"].append({
                    "name": product.get("product_name", "Unknown"),
                    "price": product.get("price", "Unknown"),
                    "store": product.get("store_name", "Unknown"),
                    "description": product.get("description", "")[:100],
                    "reason_kept": reason
                })
    
    def track_final_results(self, final_products: List[Dict]):
        """Track final results shown to user"""
        stage = self.funnel_data["stages"]["final"]
        stage["count"] = len(final_products)
        
        for product in final_products:
            stage["products"].append({
                "name": product.get("product_name", "Unknown"),
                "price": product.get("price", "Unknown"),
                "store": product.get("store_name", "Unknown"),
                "image_url": product.get("image_url", ""),
                "product_url": product.get("product_url", "")
            })
        
        print(f"🔍 FUNNEL: Final results - {len(final_products)} products")
    
    def track_timing(self, stage_name: str, duration: float):
        """Track timing for different stages"""
        self.funnel_data["timing"]["stage_durations"][stage_name] = duration
    
    def track_error(self, error: str, context: str = ""):
        """Track errors during the funnel"""
        self.funnel_data["errors"].append({
            "error": str(error),
            "context": context,
            "timestamp": time.time() - self.start_time
        })
    
    def finalize_and_generate_report(self):
        """Generate the complete funnel visualization report"""
        self.funnel_data["timing"]["total_duration"] = time.time() - self.start_time
        
        # Generate multiple report formats
        self._generate_text_report()
        self._generate_json_report()
        self._generate_detailed_analysis()
        
        print(f"🔍 FUNNEL: Reports generated in {self.output_dir}")
        print(f"🔍 FUNNEL: Session ID: {self.session_id}")
    
    def _generate_text_report(self):
        """Generate human-readable text report"""
        report_path = self.output_dir / f"funnel_report_{self.session_id}.txt"
        
        with open(report_path, 'w') as f:
            f.write(f"""
SHOPIFY PRODUCT FILTERING FUNNEL REPORT
=======================================

Query: "{self.query}"
Session ID: {self.session_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Duration: {self.funnel_data['timing']['total_duration']:.2f} seconds

FUNNEL OVERVIEW
===============
""")
            
            stages = self.funnel_data["stages"]
            raw_count = stages["raw"]["count"]
            prefiltered_count = stages["prefiltered"]["count"]
            llm_filtered_count = stages["llm_filtered"]["count"]
            final_count = stages["final"]["count"]
            
            f.write(f"""
Raw Shopify Data:     {raw_count:,} products
↓ Prefiltering:       {prefiltered_count:,} products ({self._percentage(prefiltered_count, raw_count)})
↓ LLM Filtering:      {llm_filtered_count:,} products ({self._percentage(llm_filtered_count, prefiltered_count)})
↓ Final Selection:    {final_count:,} products ({self._percentage(final_count, llm_filtered_count)})

CONVERSION RATES
================
Raw → Prefiltered:   {self._percentage(prefiltered_count, raw_count)}
Prefiltered → LLM:   {self._percentage(llm_filtered_count, prefiltered_count)}
LLM → Final:         {self._percentage(final_count, llm_filtered_count)}
Overall:             {self._percentage(final_count, raw_count)}

STORES SEARCHED
===============
""")
            
            for i, store in enumerate(self.funnel_data["stores_searched"], 1):
                f.write(f"{i}. {store}\n")
            
            f.write(f"""
STAGE ANALYSIS
==============

1. RAW DATA ANALYSIS
--------------------
Total products extracted: {raw_count:,}
Sample products (first 10):
""")
            
            for i, product in enumerate(stages["raw"]["products"][:10], 1):
                f.write(f"  {i}. {product['title']} - {product['product_type']} - ${product['first_variant_price']}\n")
                f.write(f"     Store: {product['store']} | Variants: {product['variants_count']}\n")
                if product['tags']:
                    f.write(f"     Tags: {', '.join(product['tags'])}\n")
                f.write("\n")
            
            f.write(f"""
2. PREFILTERING ANALYSIS
-------------------------
Products kept: {prefiltered_count:,} / {raw_count:,} ({self._percentage(prefiltered_count, raw_count)})

Recent prefiltering decisions:
""")
            
            # Show both kept and removed decisions
            kept_decisions = [d for d in stages["prefiltered"]["decisions"] if d["action"] == "kept"][-10:]
            removed_decisions = [d for d in stages["prefiltered"]["decisions"] if d["action"] == "removed"][-10:]
            
            f.write("\nKEPT (last 10):\n")
            for decision in kept_decisions:
                f.write(f"  ✅ {decision['product_title']} - {decision['reason']}\n")
            
            f.write("\nREMOVED (last 10):\n")
            for decision in removed_decisions:
                f.write(f"  ❌ {decision['product_title']} - {decision['reason']}\n")
            
            f.write(f"""

3. LLM FILTERING ANALYSIS
--------------------------
Products kept: {llm_filtered_count:,} / {prefiltered_count:,} ({self._percentage(llm_filtered_count, prefiltered_count)})

Recent LLM decisions:
""")
            
            llm_kept = [d for d in stages["llm_filtered"]["decisions"] if d["action"] == "kept"][-10:]
            llm_removed = [d for d in stages["llm_filtered"]["decisions"] if d["action"] == "removed"][-10:]
            
            f.write("\nKEPT (last 10):\n")
            for decision in llm_kept:
                f.write(f"  ✅ {decision['product_name']} - {decision['reason']}\n")
            
            f.write("\nREMOVED (last 10):\n")
            for decision in llm_removed:
                f.write(f"  ❌ {decision['product_name']} - {decision['reason']}\n")
            
            f.write(f"""

4. FINAL RESULTS
----------------
Products shown to user: {final_count}

Final products:
""")
            
            for i, product in enumerate(stages["final"]["products"], 1):
                f.write(f"  {i}. {product['name']} - {product['price']}\n")
                f.write(f"     Store: {product['store']}\n")
                if product['product_url']:
                    f.write(f"     URL: {product['product_url']}\n")
                f.write("\n")
            
            if self.funnel_data["errors"]:
                f.write(f"""
ERRORS ENCOUNTERED
==================
""")
                for error in self.funnel_data["errors"]:
                    f.write(f"- {error['context']}: {error['error']}\n")
            
            f.write(f"""
TIMING BREAKDOWN
================
""")
            for stage, duration in self.funnel_data["timing"]["stage_durations"].items():
                f.write(f"{stage}: {duration:.2f}s\n")
        
        print(f"📊 Text report saved: {report_path}")
    
    def _generate_json_report(self):
        """Generate machine-readable JSON report"""
        json_path = self.output_dir / f"funnel_data_{self.session_id}.json"
        
        with open(json_path, 'w') as f:
            json.dump(self.funnel_data, f, indent=2, default=str)
        
        print(f"📊 JSON data saved: {json_path}")
    
    def _generate_detailed_analysis(self):
        """Generate detailed analysis with insights"""
        analysis_path = self.output_dir / f"funnel_analysis_{self.session_id}.txt"
        
        stages = self.funnel_data["stages"]
        raw_count = stages["raw"]["count"]
        prefiltered_count = stages["prefiltered"]["count"]
        llm_filtered_count = stages["llm_filtered"]["count"]
        final_count = stages["final"]["count"]
        
        with open(analysis_path, 'w') as f:
            f.write(f"""
DETAILED FUNNEL ANALYSIS
========================

Query: "{self.query}"
Session: {self.session_id}

POTENTIAL ISSUES DETECTED
==========================
""")
            
            # Analyze for potential issues
            if raw_count == 0:
                f.write("🚨 CRITICAL: No raw data extracted from Shopify stores\n")
            elif raw_count < 10:
                f.write(f"⚠️  WARNING: Very low raw data count ({raw_count})\n")
            
            prefilter_rate = prefiltered_count / raw_count if raw_count > 0 else 0
            if prefilter_rate < 0.1:
                f.write(f"⚠️  WARNING: Very aggressive prefiltering ({prefilter_rate:.1%} kept)\n")
            elif prefilter_rate > 0.8:
                f.write(f"⚠️  WARNING: Prefiltering may be too lenient ({prefilter_rate:.1%} kept)\n")
            
            llm_rate = llm_filtered_count / prefiltered_count if prefiltered_count > 0 else 0
            if llm_rate < 0.2:
                f.write(f"⚠️  WARNING: Very aggressive LLM filtering ({llm_rate:.1%} kept)\n")
            elif llm_rate > 0.9:
                f.write(f"⚠️  WARNING: LLM filtering may be too lenient ({llm_rate:.1%} kept)\n")
            
            if final_count == 0:
                f.write("🚨 CRITICAL: No final products to show user\n")
            elif final_count < 3:
                f.write(f"⚠️  WARNING: Very few final products ({final_count})\n")
            
            f.write(f"""

FILTERING EFFECTIVENESS
=======================

Prefiltering Stage:
- Input: {raw_count:,} products
- Output: {prefiltered_count:,} products  
- Rejection rate: {100 - self._percentage_raw(prefiltered_count, raw_count):.1f}%
- Top rejection reasons:
""")
            
            # Analyze rejection reasons
            rejection_reasons = {}
            for decision in stages["prefiltered"]["decisions"]:
                if decision["action"] == "removed":
                    reason = decision["reason"]
                    rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
            
            for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
                f.write(f"  - {reason}: {count} products\n")
            
            f.write(f"""

LLM Filtering Stage:
- Input: {prefiltered_count:,} products
- Output: {llm_filtered_count:,} products
- Rejection rate: {100 - self._percentage_raw(llm_filtered_count, prefiltered_count):.1f}%
- Top rejection reasons:
""")
            
            llm_rejection_reasons = {}
            for decision in stages["llm_filtered"]["decisions"]:
                if decision["action"] == "removed":
                    reason = decision["reason"]
                    llm_rejection_reasons[reason] = llm_rejection_reasons.get(reason, 0) + 1
            
            for reason, count in sorted(llm_rejection_reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
                f.write(f"  - {reason}: {count} products\n")
            
            f.write(f"""

RECOMMENDATIONS
===============
""")
            
            if prefilter_rate < 0.2:
                f.write("- Consider relaxing prefiltering rules to allow more products through\n")
            if llm_rate < 0.3:
                f.write("- Consider adjusting LLM filtering criteria to be less aggressive\n")
            if final_count < 5:
                f.write("- Consider expanding search to more stores or relaxing filters\n")
            if raw_count < 50:
                f.write("- Consider searching additional Shopify stores for better coverage\n")
        
        print(f"📊 Analysis saved: {analysis_path}")
    
    def _percentage(self, part: int, total: int) -> str:
        """Calculate percentage as string"""
        if total == 0:
            return "0.0%"
        return f"{(part / total) * 100:.1f}%"
    
    def _percentage_raw(self, part: int, total: int) -> float:
        """Calculate percentage as float"""
        if total == 0:
            return 0.0
        return (part / total) * 100


# Global instance for easy access
_funnel_visualizer: Optional[FunnelVisualizer] = None

def init_funnel_tracking(query: str) -> FunnelVisualizer:
    """Initialize funnel tracking for a query or reuse existing one for the same query"""
    global _funnel_visualizer
    
    # Check if we already have an active session for the same query
    if _funnel_visualizer and _funnel_visualizer.query == query:
        print(f"🔍 FUNNEL: Reusing existing session for query: '{query}'")
        return _funnel_visualizer
    
    _funnel_visualizer = FunnelVisualizer(query)
    return _funnel_visualizer

def get_funnel_visualizer() -> Optional[FunnelVisualizer]:
    """Get the current funnel visualizer"""
    return _funnel_visualizer

def finalize_funnel_tracking():
    """Finalize and generate reports"""
    global _funnel_visualizer
    if _funnel_visualizer:
        _funnel_visualizer.finalize_and_generate_report()
        _funnel_visualizer = None 