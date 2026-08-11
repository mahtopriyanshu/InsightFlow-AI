"""Live golden-question, filter-scope, read-only, and performance validation."""
from datetime import date
from pathlib import Path
from time import perf_counter
import math,sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from streamlit_app.assistant import ask_assistant
from streamlit_app.assistant.executor import execute_read_only
from streamlit_app.services.common import get_filter_options
from streamlit_app.services.operations import get_delivery_metrics,get_review_metrics
from streamlit_app.services.overview import get_category_performance,get_kpis,get_monthly_performance,get_payment_methods,get_state_performance
from streamlit_app.services.portfolio import get_category_analytics,get_seller_analytics
from streamlit_app.utils.filters import FilterState


def close(a,b,tol=1e-6): assert math.isclose(float(a),float(b),rel_tol=tol,abs_tol=tol),(a,b)


def golden(filters):
    k=get_kpis(filters).iloc[0];delivery=get_delivery_metrics(filters).iloc[0];reviews=get_review_metrics(filters).iloc[0]
    answers={q:ask_assistant(q,filters,use_llm=False) for q in (
      "What is total revenue?","How many total orders?","How many unique customers do we have?","What is average order value?",
      "What are the top 5 categories by revenue?","Which states generate the most revenue?","Show monthly revenue trend.",
      "What payment method is used most?","What is delivery rate?","What is late-delivery rate?","What is our average review score?",
      "What is negative-review rate?","Which sellers generate the most merchandise revenue?","Which categories have poor reviews?","Compare SP and RJ by revenue.")}
    close(answers["What is total revenue?"].data.iloc[0,0],k.total_revenue);close(answers["How many total orders?"].data.iloc[0,0],k.total_orders)
    close(answers["How many unique customers do we have?"].data.iloc[0,0],k.unique_customers);close(answers["What is average order value?"].data.iloc[0,0],k.average_order_value)
    close(answers["What is delivery rate?"].data.iloc[0,0],delivery.delivery_rate);close(answers["What is late-delivery rate?"].data.iloc[0,0],delivery.late_rate)
    close(answers["What is our average review score?"].data.iloc[0,0],reviews.average_review_score);close(answers["What is negative-review rate?"].data.iloc[0,0],reviews.negative_review_rate)
    categories=get_category_performance(filters,5);close(answers["What are the top 5 categories by revenue?"].data.iloc[0].merchandise_revenue,categories.iloc[0].revenue)
    states=get_state_performance(filters);close(answers["Which states generate the most revenue?"].data.iloc[0].payment_revenue,states.iloc[0].revenue)
    monthly=get_monthly_performance(filters);close(answers["Show monthly revenue trend."].data.payment_revenue.sum(),monthly.revenue.sum())
    payments=get_payment_methods(filters).sort_values(["orders","payment_value"],ascending=False);assert answers["What payment method is used most?"].data.iloc[0].payment_type==payments.iloc[0].payment_type
    sellers=get_seller_analytics(filters);close(answers["Which sellers generate the most merchandise revenue?"].data.iloc[0].merchandise_revenue,sellers.iloc[0].merchandise_revenue)
    cat=get_category_analytics(filters);qual=cat.loc[cat.reviews>=30].sort_values("average_review_score");assert answers["Which categories have poor reviews?"].data.iloc[0].category==qual.iloc[0].category
    assert set(answers["Compare SP and RJ by revenue."].data.state)=={"SP","RJ"}
    assert all(answer.evidence.row_count<=100 and answer.evidence.llm_calls==0 for answer in answers.values())
    return {question:answer.intent for question,answer in answers.items()}


def main():
    lo,hi,_,cats=get_filter_options();cat="health_beauty" if "health_beauty" in cats else cats[0];period=(date(2018,1,1),date(2018,3,31))
    contexts={"full":FilterState(lo,hi),"date":FilterState(*period),"SP":FilterState(lo,hi,("SP",)),"category":FilterState(lo,hi,(),(cat,)),"date_SP":FilterState(*period,("SP",)),"date_category":FilterState(*period,(),(cat,)),"date_SP_category":FilterState(*period,("SP",),(cat,))}
    started=perf_counter();intents=golden(contexts["full"]);cold=perf_counter()-started;print("golden",{"passed":len(intents),"seconds":round(cold,3),"intents":intents})
    for name,filters in contexts.items():
        expected=get_kpis(filters).iloc[0].total_revenue;answer=ask_assistant("What is total revenue?",filters,use_llm=False);close(answer.data.iloc[0,0],expected);print(name,{"scope":answer.scope,"revenue":round(float(expected),2),"sql_ms":round(answer.evidence.execution_ms,2)})
    started=perf_counter();ask_assistant("What is total revenue?",contexts["full"],use_llm=False);print("cached_seconds",round(perf_counter()-started,4))
    setting,_=execute_read_only("SHOW transaction_read_only",());assert str(setting.iloc[0,0]).lower()=="on";print("assistant_transaction_read_only",setting.iloc[0,0])
if __name__=="__main__":main()
