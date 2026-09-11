import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# Streamlit 페이지 기본 설정
st.set_page_config(page_title="일자별 박스오피스", layout="wide")

st.title("🎬 박스오피스 조회")


# --- [1] 데이터 불러오기 함수 (캐싱 적용) ---
# ttl=3600: 같은 날짜를 다시 조회할 경우 1시간 동안 API를 재호출하지 않고 저장된 결과를 사용합니다.
@st.cache_data(ttl=3600)
def fetch_box_office(target_date, api_key):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None, f"API 요청에 실패했습니다. (응답 코드: {response.status_code})"

        data = response.json()

        # KOBIS API faultInfo 예외 처리
        if "faultInfo" in data:
            fault_msg = data["faultInfo"].get("message", "알 수 없는 오류")
            return None, f"KOBIS API 오류가 발생했습니다: {fault_msg}"

        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        # 영화 목록이 비어있는 경우
        if not daily_list:
            return None, "EMPTY_LIST"

        return daily_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 에러가 발생했습니다: {str(e)}"


# --- [2] 인증키 설정 및 검증 ---
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "💡 **[안내] API 키 설정 필요**\n\n"
        "Streamlit Cloud의 App Settings > Secrets에서 `KOBIS_KEY`를 설정해 주세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]


# --- [3] 날짜 선택기 (KST 기준 최대로 선택 가능한 날짜 = 어제) ---
kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst).date()
yesterday = now_kst - datetime.timedelta(days=1)

# 달력 입력 UI (기본값: 어제, 최대 선택 가능일: 어제)
selected_date = st.date_input(
    "조회할 날짜를 선택하세요 (오늘 날짜는 아직 집계 전입니다)",
    value=yesterday,
    max_value=yesterday,
    min_value=datetime.date(2004, 1, 1),  # KOBIS 데이터 제공 시작 시점
)

target_date_str = selected_date.strftime("%Y%m%d")
display_date_str = selected_date.strftime("%Y년 %m월 %d일")

st.caption(f"선택한 일자: **{display_date_str}**")


# --- [4] API 데이터 수집 및 예외 처리 ---
daily_list, error_message = fetch_box_office(target_date_str, api_key)

if error_message:
    # 영화 목록이 비어서 온 경우 특정 안내문 출력
    if error_message == "EMPTY_LIST":
        st.info("💡 **선택하신 날짜는 아직 집계 전입니다.** 다른 날짜를 선택해 주세요.")
    else:
        st.error(
            f"⚠️ **데이터를 불러오지 못했습니다.**\n\n"
            f"**상세 내용:** {error_message}\n\n"
            "**확인해야 할 사항:**\n"
            "1. `KOBIS_KEY`가 올바르게 등록되었는지 확인해 주세요.\n"
            "2. 영화진흥위원회(KOBIS) API 서비스가 정상 작동 중인지 확인해 주세요."
        )
    st.stop()


# --- [5] 데이터 전처리 (문자열 -> 숫자 변환 및 텍스트 처리) ---
df = pd.DataFrame(daily_list)

# 숫자형으로 변환할 칼럼들
numeric_columns = [
    "rank",
    "rankInten",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
    "showCnt",
]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# 1. 누적 관객수 100만 이상시 트로피 이모지(🏆) 추가
df["movieNm_display"] = df.apply(
    lambda x: f"{x['movieNm']} 🏆" if x["audiAcc"] >= 1_000_000 else x["movieNm"],
    axis=1,
)

# 2. rankInten(순위 증감) 값에 따라 빨간 위 화살표 / 파란 아래 화살표 표기
def format_rank_change(val):
    if val > 0:
        return f"🔺 {val}"  # 상승 (빨간 위 화살표)
    elif val < 0:
        return f"🔹 {abs(val)}"  # 하락 (파란 아래 화살표)
    else:
        return "-"  # 변동 없음

df["rankInten_display"] = df["rankInten"].apply(format_rank_change)


# --- [6] 1위 영화 핵심 지표 (Metric Card) ---
top_1 = df[df["rank"] == 1].iloc[0]

# 1위 영화 순위 변동 텍스트
rank_inten = top_1["rankInten"]
if rank_inten > 0:
    rank_delta = f"▲ {rank_inten} (순위 상승)"
elif rank_inten < 0:
    rank_delta = f"▼ {abs(rank_inten)} (순위 하락)"
else:
    rank_delta = "– (순위 유지)"

st.markdown(f"### 🏆 선택한 날짜의 1위 영화: **{top_1['movieNm_display']}**")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="당일 관객수",
        value=f"{top_1['audiCnt']:,} 명",
        delta=rank_delta,
    )
with col2:
    st.metric(
        label="누적 관객수",
        value=f"{top_1['audiAcc']:,} 명",
    )
with col3:
    st.metric(
        label="스크린수",
        value=f"{top_1['scrnCnt']:,} 개",
    )

st.divider()


# --- [7] 상위 5개 영화 관객수 막대그래프 ---
st.subheader("📊 관객수 TOP 5")
top5_df = df.sort_values(by="rank").head(5)

chart_df = top5_df[["movieNm", "audiCnt"]].set_index("movieNm")
chart_df.columns = ["관객수"]

st.bar_chart(chart_df)

st.divider()


# --- [8] 전체 순위 표 출력 ---
st.subheader("📋 전체 박스오피스 순위")

# 화면 출력용 데이터프레임 구성
display_df = df[
    [
        "rank",
        "rankInten_display",
        "movieNm_display",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt",
    ]
].copy()

display_df.columns = [
    "순위",
    "전일대비",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객수",
    "스크린수",
]

# 관객수/스크린수에 천 단위 쉼표 서식 적용
formatted_df = display_df.copy()
formatted_df["관객수"] = formatted_df["관객수"].apply(lambda x: f"{x:,}")
formatted_df["누적관객수"] = formatted_df["누적관객수"].apply(lambda x: f"{x:,}")
formatted_df["스크린수"] = formatted_df["스크린수"].apply(lambda x: f"{x:,}")

st.dataframe(formatted_df, use_container_width=True, hide_index=True)
