import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="영화 데이터 그래프 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

# 앱 제목
st.title("🎬 영화 데이터 그래프 - 분포와 관계")
st.markdown("1년간 박스오피스 10위권에 든 영화(216편) 데이터 분석 결과입니다.")

# 데이터 로드 및 전처리 함수
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    
    # openDt 컬럼 문자열 변환
    df['openDt'] = df['openDt'].astype(str)
    
    # genre 전처리: 세로막대 기호(|)로 여러 개 적힌 영화는 첫 번째 장르만 사용
    df['genre_clean'] = df['genre'].astype(str).apply(lambda x: x.split('|')[0].strip() if pd.notna(x) else '미상')
    
    return df

# 데이터 불러오기
try:
    df = load_data()
    st.success("데이터를 성공적으로 불러왔습니다!")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 사이드바 데이터 확인
with st.sidebar:
    st.header("📊 데이터 정보")
    st.write(f"총 영화 수: **{len(df)}편**")
    if st.checkbox("원본 데이터 보기"):
        st.dataframe(df)

# ---------------------------------------------------------
# 구역 1: 장르별 영화 편수 (도넛 그래프)
# ---------------------------------------------------------
st.header("1. 장르별 영화 편수 분포")

# 장르별 편수 집계
genre_counts = df['genre_clean'].value_counts().reset_index()
genre_counts.columns = ['장르', '영화 편수']

# Plotly 도넛 차트 생성
fig_donut = px.pie(
    genre_counts,
    names='장르',
    values='영화 편수',
    hole=0.4,
    title='장르별 영화 편수 비율',
    color_discrete_sequence=px.colors.qualitative.Pastel
)

# 마우스 오버(Hover) 시 편수와 비율이 함께 보이도록 설정
fig_donut.update_traces(
    textinfo='percent+label',
    hovertemplate='<b>장르:</b> %{label}<br><b>영화 편수:</b> %{value}편<br><b>비율:</b> %{percent}<extra></extra>'
)

fig_donut.update_layout(
    margin=dict(t=50, b=20, l=20, r=20),
    legend_title_text='장르'
)

# 차트 출력
st.plotly_chart(fig_donut, use_container_width=True)

# 그래프 설명 구역
st.divider()
st.info("💡 **이 그래프로 알 수 있는 것:** 국내 박스오피스 상위권에 진입한 영화들은 특정 주요 장르에 집중되어 있으며, 전체적인 장르별 분포와 비중을 한눈에 파악할 수 있습니다.")

st.markdown("---")

# ---------------------------------------------------------
# 구역 2: 흥행 지표 관계 분석 (관객 수 및 유지가간)
# ---------------------------------------------------------
st.header("2. 관객 수 및 흥행 지표 관계 분석")

col1, col2 = st.columns(2)

with col1:
    fig_scatter = px.scatter(
        df,
        x='first_week_audi',
        y='total_audi',
        color='genre_clean',
        hover_name='movieNm',
        labels={'first_week_audi': '개봉 첫 주 관객 수', 'total_audi': '총 관객 수', 'genre_clean': '장르'},
        title='개봉 첫 주 관객 수 vs 총 관객 수'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.info("💡 **이 그래프로 알 수 있는 것:** 개봉 첫 주 관객 수가 높은 영화일수록 최종 총 관객 수 역시 비례하여 증가하는 강한 양의 상관관계를 보입니다.")

with col2:
    fig_hist = px.histogram(
        df,
        x='days_in_top10',
        nbins=20,
        title='TOP10 유지 기간(일수) 분포',
        labels={'days_in_top10': 'TOP10 머문 날수', 'count': '영화 수'},
        color_discrete_sequence=['#636EFA']
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    st.info("💡 **이 그래프로 알 수 있는 것:** 대부분의 박스오피스 상위권 영화는 특정 일정 기간 내에 집중적으로 TOP10에 머무르며 흥행 수명을 유지합니다.")
