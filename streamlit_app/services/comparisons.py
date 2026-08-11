"""PostgreSQL-backed snapshots for M15 comparisons."""
from datetime import date
import pandas as pd
from streamlit_app.comparisons import ComparisonResult,build_result
from streamlit_app.insights.comparisons import previous_comparable_period,scope_label
from streamlit_app.services.common import get_filter_options,filtered_orders_cte
from streamlit_app.database.connection import query_dataframe
from streamlit_app.services.customers import get_customer_metrics
from streamlit_app.services.operations import get_delivery_metrics,get_review_metrics
from streamlit_app.services.overview import get_kpis
from streamlit_app.services.portfolio import get_category_analytics,get_category_seller_concentration,get_seller_analytics
from streamlit_app.utils.filters import FilterState

PERIOD_SPECS=(
 ("Payment Revenue","revenue","percent","currency","higher","Sum of validated order payment revenue"),("Orders","orders","percent","count","higher","Distinct filtered orders"),("Unique Customers","unique_customers","percent","count","higher","Distinct customer_unique_id"),("Average Order Value","aov","percent","currency","neutral","Payment revenue divided by orders"),("Revenue per Customer","revenue_per_customer","percent","currency","neutral","Payment revenue per unique customer"),("Delivery Rate","delivery_rate","percentage_points","percentage","higher","Delivered orders divided by selected orders"),("Late Delivery Rate","late_rate","percentage_points","percentage","lower","Late divided by eligible delivered outcomes"),("Average Delivery Days","delivery_days","days","days","lower","Average actual delivery duration"),("Average Review Score","review_score","points","score","higher","Average order review score"),("Negative Review Rate","negative_review_rate","percentage_points","percentage","lower","Reviews scored one or two"),)
CATEGORY_SPECS=(("Merchandise Revenue","revenue","percent","currency","higher","Sum of order-item price"),("Orders","orders","percent","count","higher","Distinct category orders"),("Units Sold","units","percent","count","higher","Order-item rows"),("Products Represented","products","percent","count","neutral","Distinct product IDs"),("Sellers Represented","sellers","percent","count","neutral","Distinct sellers in category"),("Average Item Price","average_item_price","percent","currency","neutral","Average item price"),("Freight / Merchandise","freight_ratio","percentage_points","percentage","lower","Freight divided by merchandise revenue"),("Average Review Score","review_score","points","score","higher","Deduplicated order-category reviews"),("Late Delivery Rate","late_rate","percentage_points","percentage","lower","Order-category eligible late rate"),("Revenue Contribution","revenue_share","percentage_points","percentage","neutral","Share of selected merchandise revenue"),("Top Seller Share","top_seller_share","percentage_points","percentage","lower","Largest seller share of category revenue"),)
SELLER_SPECS=(("Merchandise Revenue","revenue","percent","currency","higher","Sum of seller order-item price"),("Orders","orders","percent","count","higher","Distinct seller orders"),("Units Sold","units","percent","count","higher","Seller order-item rows"),("Categories Served","categories","percent","count","neutral","Distinct represented categories"),("Late Delivery Rate","late_rate","percentage_points","percentage","lower","Order-seller eligible late rate"),("Fulfillment Rate","delivery_rate","percentage_points","percentage","higher","Delivered seller orders divided by orders"),("Revenue Contribution","revenue_share","percentage_points","percentage","neutral","Share of selected seller merchandise revenue"),("Order-level Experience Proxy","review_score","points","score","neutral","Order review attributed once per order-seller"),)

def period_snapshot(filters):
    k=get_kpis(filters).iloc[0];c=get_customer_metrics(filters).iloc[0];d=get_delivery_metrics(filters).iloc[0];r=get_review_metrics(filters).iloc[0]
    return {"revenue":k.total_revenue,"orders":k.total_orders,"unique_customers":k.unique_customers,"aov":k.average_order_value,"revenue_per_customer":c.revenue_per_customer,"repeat_rate":c.repeat_rate,"delivery_rate":d.delivery_rate,"late_rate":d.late_rate,"delivery_days":d.average_delivery_days,"review_score":r.average_review_score,"negative_review_rate":r.negative_review_rate},int(k.total_orders)

def compare_periods(filters:FilterState)->ComparisonResult:
    earliest,*_=get_filter_options();comparison=previous_comparable_period(filters,earliest)
    if not comparison.available:return ComparisonResult("Period vs Period","Selected period","Previous comparable period",(),scope=scope_label(filters),available=False,reason=comparison.reason or "Comparable period unavailable")
    left,ls=period_snapshot(filters);right,rs=period_snapshot(comparison.previous)
    return build_result("Period vs Period",f"{filters.start_date:%d %b %Y} – {filters.end_date:%d %b %Y}",f"{comparison.previous.start_date:%d %b %Y} – {comparison.previous.end_date:%d %b %Y}",left,right,PERIOD_SPECS,scope_label(filters),ls,rs)

def compare_categories(filters:FilterState,left_label:str,right_label:str)->ComparisonResult:
    base=FilterState(filters.start_date,filters.end_date,filters.states,())
    all_categories=get_category_analytics(base);total=float(all_categories.merchandise_revenue.sum())
    cross=get_category_seller_concentration(base).set_index("category")
    def snap(label):
        row=all_categories.loc[all_categories.category.eq(label)].iloc[0];x=cross.loc[label]
        return {"revenue":row.merchandise_revenue,"orders":row.orders,"units":row.units,"products":row.products,"sellers":x.sellers,"average_item_price":row.average_item_price,"freight_ratio":row.freight_ratio,"review_score":row.average_review_score,"late_rate":row.late_rate,"revenue_share":100*float(row.merchandise_revenue)/max(total,1),"top_seller_share":x.top_seller_share},int(row.orders)
    l,ls=snap(left_label);r,rs=snap(right_label)
    return build_result("Category vs Category",left_label,right_label,l,r,CATEGORY_SPECS,scope_label(base),ls,rs)

def compare_states(filters:FilterState,left_label:str,right_label:str)->ComparisonResult:
    def snap(label):return period_snapshot(FilterState(filters.start_date,filters.end_date,(label,),filters.categories))
    l,ls=snap(left_label);r,rs=snap(right_label)
    return build_result("Destination State vs State",left_label,right_label,l,r,PERIOD_SPECS,scope_label(FilterState(filters.start_date,filters.end_date,(),filters.categories)),ls,rs)

def compare_sellers(filters:FilterState,left_label:str,right_label:str)->ComparisonResult:
    sellers=get_seller_analytics(filters);total=float(sellers.merchandise_revenue.sum())
    cte,params=filtered_orders_cte(filters)
    counts=query_dataframe(cte+"""SELECT i.seller_id,COUNT(DISTINCT COALESCE(t.product_category_name_english,p.product_category_name)) categories FROM filtered_orders f JOIN olist_analytics.order_items i USING(order_id) JOIN olist_analytics.products p USING(product_id) LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name) WHERE i.seller_id IN (%s,%s) GROUP BY i.seller_id""",(*params,left_label,right_label)).set_index("seller_id")
    def snap(label):
        row=sellers.loc[sellers.seller_id.eq(label)].iloc[0]
        return {"revenue":row.merchandise_revenue,"orders":row.orders,"units":row.units,"categories":counts.loc[label,"categories"] if label in counts.index else None,"late_rate":row.late_rate,"delivery_rate":row.delivery_rate,"revenue_share":100*float(row.merchandise_revenue)/max(total,1),"review_score":row.average_review_score},int(row.orders)
    l,ls=snap(left_label);r,rs=snap(right_label)
    return build_result("Seller vs Seller",left_label,right_label,l,r,SELLER_SPECS,scope_label(filters),ls,rs)
