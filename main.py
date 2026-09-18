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
    
    # openDt 컬럼을 문자열로 변환
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
# 첫 번째 그래프: 장르별 영화 편수 (도넛 그래프)
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

# 마우스 오버(Hover) 시 편수와 비율 표시
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

# 구분선 및 분석 설명 구역
st.divider()
st.info("💡 **이 그래프로 알 수 있는 것:** 국내 박스오피스 상위권에 진입한 영화들의 장르별 비중과 편수 분포를 한눈에 파악할 수 있습니다.")

st.markdown("---")

# ---------------------------------------------------------
# 두 번째 그래프: 장르 및 영화별 총 관객 수 (트리맵)
# ---------------------------------------------------------
st.header("2. 장르 및 영화별 총 관객 수 분포 (트리맵)")

# Plotly 트리맵 생성 (계층 구조: 장르 -> 영화명, 크기: total_audi)
fig_treemap = px.treemap(
    df,
    path=[px.Constant("전체"), 'genre_clean', 'movieNm'],
    values='total_audi',
    title='장르 및 영화별 총 관객 수 (트리맵)',
    color='genre_clean',
    color_discrete_sequence=px.colors.qualitative.Set3
)

# 마우스 오버(Hover) 시 영화명과 총 관객 수 표시
fig_treemap.update_traces(
    hovertemplate='<b>영화명 / 구분:</b> %{label}<br><b>총 관객 수:</b> %{value:,.0f}명<extra></extra>'
)

fig_treemap.update_layout(
    margin=dict(t=50, b=20, l=20, r=20)
)

# 차트 출력
st.plotly_chart(fig_treemap, use_container_width=True)

# 구분선 및 분석 설명 구역
st.divider()
st.info("💡 **이 그래프로 알 수 있는 것:** 장르별 전체 관객 규모와 더불어 각 장르 내에서 어떤 영화가 흥행에 가장 큰 기여를 했는지 상대적 크기로 쉽게 파악할 수 있습니다.")
