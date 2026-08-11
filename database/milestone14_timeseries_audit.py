"""Read-only audit of monthly history depth and partial periods for M14."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from streamlit_app.database.connection import query_dataframe

def show(title,df):print(f"\n## {title}\n{df.to_string(index=False)}")
def main():
 show("Dataset boundaries",query_dataframe("""SELECT MIN(order_purchase_timestamp) first_order,MAX(order_purchase_timestamp) last_order,COUNT(DISTINCT date_trunc('month',order_purchase_timestamp)) months FROM olist_analytics.orders"""))
 show("Monthly executive depth",query_dataframe("""SELECT date_trunc('month',o.order_purchase_timestamp)::date AS month,COUNT(*) orders,COUNT(DISTINCT c.customer_unique_id) customers,SUM(v.payment_revenue) revenue,AVG(v.payment_revenue) aov,MIN(o.order_purchase_timestamp)::date first_day,MAX(o.order_purchase_timestamp)::date last_day FROM olist_analytics.orders o JOIN olist_analytics.customers c USING(customer_id) LEFT JOIN olist_analytics.vw_order_revenue v USING(order_id) GROUP BY 1 ORDER BY 1"""))
 show("Category history depth",query_dataframe("""WITH x AS(SELECT COALESCE(t.product_category_name_english,p.product_category_name) AS category,date_trunc('month',o.order_purchase_timestamp)::date AS month,COUNT(DISTINCT i.order_id) orders,SUM(i.price) revenue FROM olist_analytics.order_items i JOIN olist_analytics.orders o USING(order_id) JOIN olist_analytics.products p USING(product_id) LEFT JOIN olist_analytics.product_category_translation t USING(product_category_name) GROUP BY 1,2) SELECT category,COUNT(*) months,SUM(orders) orders,SUM(revenue) revenue FROM x GROUP BY category ORDER BY revenue DESC LIMIT 15"""))
 show("Seller history depth",query_dataframe("""WITH x AS(SELECT i.seller_id,date_trunc('month',o.order_purchase_timestamp)::date AS month,COUNT(DISTINCT i.order_id) orders,SUM(i.price) revenue FROM olist_analytics.order_items i JOIN olist_analytics.orders o USING(order_id) GROUP BY 1,2) SELECT seller_id,COUNT(*) months,SUM(orders) orders,SUM(revenue) revenue FROM x GROUP BY seller_id ORDER BY revenue DESC LIMIT 15"""))
if __name__=="__main__":main()
