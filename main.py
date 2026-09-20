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

genre_counts = df['genre_clean'].value_counts().reset_index()
genre_counts.columns = ['장르', '영화 편수']

fig_donut = px.pie(
    genre_counts,
    names='장르',
    values='영화 편수',
    hole=0.4,
    title='장르별 영화 편수 비율',
    color_discrete_sequence=px.colors.qualitative.Pastel
)

fig_donut.update_traces(
    textinfo='percent+label',
    hovertemplate='<b>장르:</b> %{label}<br><b>영화 편수:</b> %{value}편<br><b>비율:</b> %{percent}<extra></extra>'
)

fig_donut.update_layout(
    margin=dict(t=50, b=20, l=20, r=20),
    legend_title_text='장르'
)

st.plotly_chart(fig_donut, use_container_width=True)

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것:** 국내 박스오피스 상위권에 진입한 영화들의 장르별 비중과 편수 분포를 한눈에 파악할 수 있습니다.")

st.markdown("---")

# ---------------------------------------------------------
# 두 번째 그래프: 장르 및 영화별 총 관객 수 (트리맵)
# ---------------------------------------------------------
st.header("2. 장르 및 영화별 총 관객 수 분포 (트리맵)")

fig_treemap = px.treemap(
    df,
    path=[px.Constant("전체"), 'genre_clean', 'movieNm'],
    values='total_audi',
    title='장르 및 영화별 총 관객 수 (트리맵)',
    color='genre_clean',
    color_discrete_sequence=px.colors.qualitative.Set3
)

fig_treemap.update_traces(
    hovertemplate='<b>영화명 / 구분:</b> %{label}<br><b>총 관객 수:</b> %{value:,.0f}명<extra></extra>'
)

fig_treemap.update_layout(
    margin=dict(t=50, b=20, l=20, r=20)
)

st.plotly_chart(fig_treemap, use_container_width=True)

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것:** 장르별 전체 관객 규모와 더불어 각 장르 내에서 어떤 영화가 흥행에 가장 큰 기여를 했는지 상대적 크기로 쉽게 파악할 수 있습니다.")

st.markdown("---")

# ---------------------------------------------------------
# 세 번째 그래프: 총 관객 수 분포 (히스토그램)
# ---------------------------------------------------------
st.header("3. 총 관객 수(total_audi) 분포")

fig_hist = px.histogram(
    df,
    x='total_audi',
    nbins=30,
    title='영화별 총 관객 수 히스토그램',
    labels={'total_audi': '총 관객 수(명)', 'count': '영화 편수'},
    color_discrete_sequence=['#636EFA']
)

fig_hist.update_traces(
    hovertemplate='<b>관객 수 구간:</b> %{x:,.0f}명<br><b>영화 편수:</b> %{y}편<extra></extra>'
)

fig_hist.update_layout(
    margin=dict(t=50, b=20, l=20, r=20),
    xaxis_title="총 관객 수 (명)",
    yaxis_title="영화 편수"
)

st.plotly_chart(fig_hist, use_container_width=True)

max_audi_movie = df.loc[df['total_audi'].idxmax()]
max_movie_name = max_audi_movie['movieNm']
max_movie_audi = max_audi_movie['total_audi']

st.divider()
st.info(f"💡 **이 그래프로 알 수 있는 것:** 대부분의 영화는 총 관객 수 200만 명 이하(하위 구간)에 밀집되어 있는 롱테일 분포를 보이며, 가장 관객 수가 많은 영화는 **'{max_movie_name}'** (약 {max_movie_audi:,.0f}명)입니다.")

st.markdown("---")

# ---------------------------------------------------------
# 네 번째 그래프: 개봉일 스크린수 vs 총 관객 수 (산점도)
# ---------------------------------------------------------
st.header("4. 개봉일 스크린수와 총 관객 수의 관계")

fig_scatter = px.scatter(
    df,
    x='first_scrn',
    y='total_audi',
    color='genre_clean',
    hover_name='movieNm',
    title='개봉일 스크린수(first_scrn) vs 총 관객 수(total_audi)',
    labels={
        'first_scrn': '개봉일 스크린수',
        'total_audi': '총 관객 수',
        'genre_clean': '장르'
    },
    hover_data={'first_scrn': ':,', 'total_audi': ':,', 'genre_clean': True}
)

fig_scatter.update_traces(
    hovertemplate='<b>영화명: %{hovertext}</b><br>장르: %{customdata[0]}<br>개봉일 스크린수: %{x:,.0f}개<br>총 관객 수: %{y:,.0f}명<extra></extra>'
)

fig_scatter.update_layout(
    margin=dict(t=50, b=20, l=20, r=20),
    xaxis_title="개봉일 스크린수 (개)",
    yaxis_title="총 관객 수 (명)"
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것:** 개봉일 스크린수가 많을수록 총 관객 수가 증가하는 대체적인 양의 상관관계를 나타내지만, 동일한 스크린수 확보 대비 흥행 성과의 격차는 장르나 작품에 따라 크게 달라짐을 알 수 있습니다.")

st.markdown("---")

# ---------------------------------------------------------
# 다섯 번째 그래프: 영화 10편 이상 장르의 총 관객 수 박스플롯
# ---------------------------------------------------------
st.header("5. 주요 장르별 총 관객 수 분포 (상자 그림)")

genre_counts = df['genre_clean'].value_counts()
top_genres = genre_counts[genre_counts >= 10].index
df_filtered = df[df['genre_clean'].isin(top_genres)]

fig_box = px.box(
    df_filtered,
    x='genre_clean',
    y='total_audi',
    color='genre_clean',
    hover_name='movieNm',
    title='영화 10편 이상 장르별 총 관객 수 상자 그림(Box Plot)',
    labels={
        'genre_clean': '장르',
        'total_audi': '총 관객 수'
    },
    points='outliers'
)

fig_box.update_traces(
    hovertemplate='<b>영화명: %{hovertext}</b><br>총 관객 수: %{y:,.0f}명<extra></extra>'
)

fig_box.update_layout(
    margin=dict(t=50, b=20, l=20, r=20),
    xaxis_title="장르",
    yaxis_title="총 관객 수 (명)",
    showlegend=False
)

st.plotly_chart(fig_box, use_container_width=True)

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것:** 영화 편수가 많은 주요 장르 간 관객 수의 중간값과 분산(격차)을 한눈에 비교할 수 있으며, 상자 밖의 아웃라이어 점들을 통해 특정 대흥행작(이상치)의 존재를 명확히 파악할 수 있습니다.")

st.markdown("---")

# ---------------------------------------------------------
# 여섯 번째 그래프: 개봉일 스크린수 vs 총 관객 수 (첫 주 관객 수 크기의 버블 그래프)
# ---------------------------------------------------------
st.header("6. 스크린수, 총 관객 수 및 첫 주 관객 수 관계 (버블 그래프)")

fig_bubble = px.scatter(
    df,
    x='first_scrn',
    y='total_audi',
    size='first_week_audi',
    color='genre_clean',
    hover_name='movieNm',
    size_max=40,
    title='개봉일 스크린수 vs 총 관객 수 (버블 크기: 개봉 첫 주 관객 수)',
    labels={
        'first_scrn': '개봉일 스크린수',
        'total_audi': '총 관객 수',
        'first_week_audi': '개봉 첫 주 관객 수',
        'genre_clean': '장르'
    },
    hover_data={'first_scrn': ':,', 'total_audi': ':,', 'first_week_audi': ':,', 'genre_clean': True}
)

fig_bubble.update_traces(
    hovertemplate='<b>영화명: %{hovertext}</b><br>장르: %{customdata[0]}<br>개봉일 스크린수: %{x:,.0f}개<br>총 관객 수: %{y:,.0f}명<br>첫 주 관객 수: %{customdata[1]:,.0f}명<extra></extra>'
)

fig_bubble.update_layout(
    margin=dict(t=50, b=20, l=20, r=20),
    xaxis_title="개봉일 스크린수 (개)",
    yaxis_title="총 관객 수 (명)"
)

st.plotly_chart(fig_bubble, use_container_width=True)

st.divider()
st.info("💡 **이 그래프로 알 수 있는 것:** 개봉일 스크린수와 최종 총 관객 수의 관계에 더해 버블 크기(첫 주 관객 수)를 통해 초반 흥행 집객력이 최종 관객 수 형성에 얼마나 결정적인 영향을 미치는지 다차원적으로 파악할 수 있습니다.")
