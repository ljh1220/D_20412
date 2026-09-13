import plotly.express as px
import pandas as pd
import streamlit as st

# 웹앱 페이지 기본 설정 (제목, 레이아웃)
st.set_page_config(page_title="박스오피스 데이터 분석", layout="wide")


# [1. 데이터 불러오기]
# @st.cache_data: 데이터를 매번 다시 다운로드하지 않고 캐시에 저장하여 재사용합니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)

    # [2. 날짜 전처리]
    # 결측치가 포함된 행 삭제
    df = df.dropna()

    # '기준일자' 컬럼을 datetime 형식으로 변환
    df["기준일자"] = pd.to_datetime(df["기준일자"])

    # 기준일자 오름차순 정렬
    df = df.sort_values(by="기준일자", ascending=True)

    return df


# 데이터 로드
df = load_data()

st.title("🎬 영화 박스오피스 데이터 분석 앱")
st.markdown("---")

# [3. 영화 선택 기능]
# 누적관객수가 가장 높은 순으로 영화 목록 정렬 (중복 제거)
# 영화별 최대 누적관객수를 기준으로 내림차순 정렬합니다.
movie_rank = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .index.tolist()
)

# 사이드바에 영화 선택 드롭다운 생성
selected_movie = st.sidebar.selectbox("영화를 선택하세요", movie_rank)

# 선택된 영화 데이터만 필터링
filtered_df = df[df["영화명"] == selected_movie]

# -------------------------------------------------------------------
# [구역 1] 일별 관객수 변화 (선그래프)
# -------------------------------------------------------------------
st.header(f"📌 1. {selected_movie} 일별 관객수 추이")

fig_daily_audience = px.line(
    filtered_df,
    x="기준일자",
    y="해당일관객수",
    title=f"[{selected_movie}] 날짜별 해당일관객수 변화",
    markers=True,  # 데이터 지점에 점 표시
    labels={"기준일자": "날짜", "해당일관객수": "일별 관객수(명)"},
)

# 그래프 호버 설정
fig_daily_audience.update_layout(hovermode="x unified")

# 화면에 출력
st.plotly_chart(fig_daily_audience, use_container_width=True)

# 그래프 설명문
st.caption("💡 **이 그래프로 알 수 있는 것:** 개봉 이후 일자별 관객수의 증감 추이와 주말/평일 간의 관객수 격차를 확인할 수 있습니다.")

st.markdown("---")

# -------------------------------------------------------------------
# [구역 2] 누적 관객수 변화 (영역차트)
# -------------------------------------------------------------------
st.header(f"📌 2. {selected_movie} 누적 관객수 추이")

# Plotly를 이용한 기준일자별 누적관객수 영역차트(area) 생성
fig_total_audience = px.area(
    filtered_df,
    x="기준일자",
    y="누적관객수",
    title=f"[{selected_movie}] 날짜별 누적관객수 증가 추이",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)"},
)

# 그래프 호버 설정
fig_total_audience.update_layout(hovermode="x unified")

# 화면에 출력
st.plotly_chart(fig_total_audience, use_container_width=True)

# 그래프 설명문
st.caption("💡 **이 그래프로 알 수 있는 것:** 시간 경과에 따라 관객수가 누적되는 가파른 정도를 통해 흥행 속도와 성수기/비수기 구간의 누적 성장세를 확인할 수 있습니다.")
