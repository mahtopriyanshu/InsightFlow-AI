"""InsightFlow AI visual design system."""
import streamlit as st

COLORS = {
    "navy": "#071426", "purple": "#6C4CF5", "blue": "#3B82F6",
    "cyan": "#14B8A6", "success": "#22C55E", "warning": "#F59E0B",
    "negative": "#EF4444", "background": "#F6F8FC",
    "card": "#FFFFFF", "muted": "#64748B", "border": "#E2E8F0",
}


def apply_theme() -> None:
    """Inject the shared responsive SaaS visual system."""
    st.markdown("""
    <style>
    html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,sans-serif}
    .stApp{background:radial-gradient(circle at 85% 0%,#fff 0,#F6F8FC 36%);color:#0F172A}
    [data-testid="stHeader"]{background:rgba(246,248,252,.88)}
    [data-testid="stSidebar"]{background:linear-gradient(180deg,#071426,#0B1B31);border:0;width:270px!important}
    [data-testid="stSidebar"] *{color:#E5E7EB}
    [data-testid="stSidebar"] [data-testid="stRadio"] label{border-radius:9px;padding:.48rem .65rem;transition:.16s ease;font-weight:550;font-size:.86rem}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover{background:rgba(108,76,245,.14);transform:translateX(2px)}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){background:linear-gradient(100deg,#2563EB,#6C4CF5);color:#fff;box-shadow:0 8px 20px rgba(108,76,245,.28)}
    [data-testid="stSidebar"] input,[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#0B1B31!important;border:1px solid #263B55!important;color:#F8FAFC!important;border-radius:9px!important}
    [data-testid="stSidebar"] [data-testid="stDateInput"] button,[data-testid="stSidebar"] svg{color:#E5E7EB!important;fill:currentColor}
    [data-testid="stSidebar"] .stButton button{background:#132942!important;border:1px solid #263B55!important;color:#fff!important}
    .block-container{max-width:1540px;padding:1.2rem 1.65rem 2.4rem}h1,h2,h3{color:#0F172A;letter-spacing:-.025em}
    .if-brand{padding:.55rem .2rem 1.05rem;display:flex;align-items:center;gap:.7rem}.if-brand-mark{width:39px;height:39px;display:grid;place-items:center;border-radius:10px;background:linear-gradient(145deg,#8B5CF6,#4F46E5);color:#fff!important;box-shadow:0 8px 20px rgba(108,76,245,.35)}
    .if-brand-title{color:#fff;font-size:1.15rem;font-weight:750}.if-brand-subtitle{color:#94A3B8;font-size:.66rem;margin-top:.08rem}.if-nav-label{font-size:.62rem;font-weight:750;letter-spacing:.12em;color:#94A3B8!important;margin:.35rem 0 .48rem}
    .if-db{display:flex;gap:.65rem;align-items:center;padding:.8rem;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);border-radius:11px}.if-db-dot{width:8px;height:8px;border-radius:50%;background:#22C55E;box-shadow:0 0 0 4px rgba(34,197,94,.13)}.if-db b{display:block;font-size:.75rem}.if-db small{display:block;color:#94A3B8;font-size:.67rem;margin-top:.1rem}
    .if-eyebrow{color:#6C4CF5;font-size:.67rem;font-weight:750;text-transform:uppercase;letter-spacing:.09em}.if-page-title{font-size:clamp(1.55rem,3vw,2rem);font-weight:780;margin:.12rem 0;letter-spacing:-.035em}.if-page-copy{color:#64748B;font-size:.86rem;margin-bottom:.65rem}
    .if-context{display:flex;gap:.45rem;flex-wrap:wrap;margin:.15rem 0 .9rem}.if-context span,.if-badge{display:inline-flex;align-items:center;padding:.28rem .55rem;border-radius:999px;background:#fff;border:1px solid #E2E8F0;color:#64748B;font-size:.68rem;font-weight:650}
    .if-kpi,.if-insight{background:#fff;border:1px solid #E2E8F0;border-radius:14px;box-shadow:0 5px 18px rgba(15,23,42,.045)}.if-kpi{padding:.85rem;min-height:118px;transition:.16s ease}.if-kpi:hover{transform:translateY(-2px);box-shadow:0 12px 26px rgba(15,23,42,.09)}
    .if-kpi-top,.if-health-row,.if-rank-row{display:flex;align-items:center;justify-content:space-between;gap:.45rem}.if-kpi-icon{display:grid;place-items:center;width:33px;height:33px;border-radius:50%;background:#F0ECFF;color:#6C4CF5;font-size:.86rem}.if-kpi-label{color:#64748B;font-size:.72rem;font-weight:650}.if-kpi-value{color:#0F172A;font-size:1.42rem;font-weight:780;margin-top:.48rem}.if-kpi-footer{display:flex;align-items:center;gap:.42rem;color:#94A3B8;font-size:.63rem;margin-top:.5rem}.if-kpi-accent{width:27px;height:3px;border-radius:4px;background:linear-gradient(90deg,#6C4CF5,#3B82F6)}
    .if-section-title{font-size:1rem;font-weight:760;color:#0F172A;margin:1rem 0 .08rem}.if-section-copy{font-size:.74rem;color:#64748B;margin-bottom:.5rem}
    .if-insight{padding:.72rem .82rem;display:flex;gap:.62rem;height:100%}.if-insight-icon{color:#6C4CF5;background:#F0ECFF;border-radius:50%;width:27px;height:27px;display:grid;place-items:center;flex:0 0 auto}.if-insight-title{font-size:.78rem;font-weight:730}.if-insight-copy{color:#64748B;font-size:.74rem;margin-top:.2rem;line-height:1.4}
    .if-insight-metric{display:inline-flex;margin-top:.45rem;padding:.18rem .42rem;border-radius:999px;background:#F0ECFF;color:#5B35E8;font-size:.64rem;font-weight:750}.if-insight.positive{border-left:3px solid #22C55E}.if-insight.warning{border-left:3px solid #F59E0B}.if-insight.critical{border-left:3px solid #EF4444}.if-insight.neutral{border-left:3px solid #94A3B8}.if-insight.informational{border-left:3px solid #6C4CF5}.if-insight.positive .if-insight-icon{background:#ECFDF5;color:#15803D}.if-insight.warning .if-insight-icon{background:#FFFBEB;color:#B45309}.if-insight.critical .if-insight-icon{background:#FEF2F2;color:#DC2626}
    .if-health,.if-ranking,.if-report{background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:.85rem;box-shadow:0 5px 18px rgba(15,23,42,.035)}.if-health-label{font-weight:720;font-size:.8rem}.if-health-help{color:#64748B;font-size:.66rem;margin-top:.12rem}.if-progress,.if-rank-bar{height:6px;background:#E8EDF5;border-radius:99px;overflow:hidden;margin-top:.72rem}.if-progress span,.if-rank-bar span{display:block;height:100%;background:linear-gradient(90deg,#6C4CF5,#8B5CF6);border-radius:99px}.if-progress .success{background:#22C55E}.if-progress .warning{background:#F59E0B}.if-progress .danger{background:#EF4444}
    .if-badge.success{background:#ECFDF5;color:#047857;border-color:#A7F3D0}.if-badge.warning{background:#FFFBEB;color:#B45309;border-color:#FDE68A}.if-badge.danger{background:#FEF2F2;color:#B91C1C;border-color:#FECACA}.if-badge.info{background:#F0ECFF;color:#5B35E8;border-color:#DDD6FE}
    .if-rank{display:flex;gap:.68rem;align-items:center;padding:.52rem 0;border-bottom:1px solid #F1F5F9}.if-rank:last-child{border:0}.if-rank-num{font-size:.66rem;font-weight:750;color:#94A3B8}.if-rank-main{flex:1}.if-rank-row{font-size:.72rem}.if-rank-row b{max-width:65%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.if-rank-bar{height:4px;margin-top:.3rem}
    .if-report{display:flex;gap:.75rem;align-items:flex-start;min-height:125px}.if-report-icon{display:grid;place-items:center;width:35px;height:35px;background:#F0ECFF;color:#6C4CF5;border-radius:10px;font-size:1.05rem}.if-report-title{font-weight:750;font-size:.82rem}.if-report-copy{font-size:.7rem;color:#64748B;margin:.2rem 0 .45rem}
    .if-assistant-hero{display:flex;gap:1rem;align-items:center;padding:1.25rem 1.4rem;border-radius:15px;background:linear-gradient(110deg,#4F46E5,#6C4CF5);box-shadow:0 12px 30px rgba(108,76,245,.2);color:#fff}.if-assistant-orb{display:grid;place-items:center;width:48px;height:48px;border-radius:14px;background:rgba(255,255,255,.16);font-size:1.35rem}.if-assistant-kicker{font-size:.62rem;font-weight:750;letter-spacing:.12em;color:#DDD6FE}.if-assistant-title{font-size:1.15rem;font-weight:760;margin:.2rem 0}.if-assistant-copy{font-size:.76rem;color:#EDE9FE;max-width:850px}.if-conversation{display:flex;gap:.7rem;padding:1rem;margin:1rem 0;background:#fff;border:1px solid #E2E8F0;border-radius:14px;min-height:95px}.if-chat-avatar{display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#F0ECFF;color:#6C4CF5}.if-chat-bubble{font-size:.78rem}.if-chat-bubble span{color:#64748B;line-height:1.5}
    .if-profile{background:linear-gradient(135deg,#fff,#FAFAFF);border:1px solid #DDD6FE;border-radius:15px;padding:1rem;box-shadow:0 8px 24px rgba(108,76,245,.07);margin:.6rem 0}.if-profile-head{display:flex;align-items:center;gap:.75rem}.if-profile-avatar{display:grid;place-items:center;width:42px;height:42px;border-radius:12px;background:linear-gradient(145deg,#6C4CF5,#3B82F6);color:#fff;font-size:1.05rem}.if-profile-label{font-size:.58rem;letter-spacing:.11em;font-weight:760;color:#6C4CF5}.if-profile-title{font-weight:760;font-size:.92rem}.if-profile-id{font-family:ui-monospace,monospace;color:#64748B;font-size:.67rem}.if-profile-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:.55rem;margin-top:.8rem}.if-profile-stat{background:#fff;border:1px solid #E2E8F0;border-radius:9px;padding:.55rem}.if-profile-stat span{display:block;color:#64748B;font-size:.62rem}.if-profile-stat b{display:block;color:#0F172A;font-size:.8rem;margin-top:.15rem}
    [data-testid="stDataFrame"],div[data-testid="stPlotlyChart"]{background:#fff;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;box-shadow:0 5px 18px rgba(15,23,42,.035)}
    .stButton>button,.stDownloadButton>button{border-radius:9px;border:1px solid #CBD5E1;font-weight:650;transition:.16s ease}.stButton>button:hover,.stDownloadButton>button:hover{border-color:#6C4CF5;color:#6C4CF5;transform:translateY(-1px)}
    @media(max-width:1100px){[data-testid="stSidebar"]{width:245px!important}.block-container{padding:1rem}.if-kpi{min-height:105px}.if-kpi-value{font-size:1.24rem}}
    </style>
    """, unsafe_allow_html=True)
