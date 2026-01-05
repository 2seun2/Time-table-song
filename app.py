import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from io import BytesIO

# ---------------------------------------------------------
# 1. 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="우리 아이 주간 시간표 (세로형)", layout="wide")

@st.cache_resource
def install_font_and_configure():
    # 폰트 설정
    font_file = "NanumGothic.ttf"
    if not os.path.exists(font_file):
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        urllib.request.urlretrieve(url, font_file)
    fm.fontManager.addfont(font_file)
    plt.rc('font', family='NanumGothic')
    plt.rcParams['axes.unicode_minus'] = False 

install_font_and_configure()

# ---------------------------------------------------------
# 2. 데이터 처리 함수
# ---------------------------------------------------------
def process_data(df):
    """ 데이터프레임을 그래프용 수치 데이터로 변환 """
    expanded_data = []
    day_order = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
    
    for index, row in df.iterrows():
        # 유효성 검사
        days_str = str(row.get('요일', '')).strip()
        start_str = str(row.get('시작시간', '')).strip()
        end_str = str(row.get('종료시간', '')).strip()
        activity_str = str(row.get('활동명', '')).strip()

        if not days_str or not start_str or not end_str or ':' not in start_str:
            continue

        days = days_str.split(',')
        
        for day in days:
            day = day.strip()
            if day in day_order:
                try:
                    s_h, s_m = map(int, start_str.split(':'))
                    e_h, e_m = map(int, end_str.split(':'))
                    
                    start_float = s_h + (s_m / 60)
                    end_float = e_h + (e_m / 60)
                    
                    color_val = str(row.get('색상', '')).strip()
                    if not color_val.startswith('#'):
                        color_val = '#CCCCCC'

                    expanded_data.append({
                        '요일': day,
                        '요일인덱스': day_order[day],
                        '활동명': activity_str,
                        '시작': start_float,       # Y축 시작 위치 (bottom)
                        '소요시간': end_float - start_float, # 막대 높이 (height)
                        '색상': color_val,
                        '시간텍스트': f"{start_str}~{end_str}"
                    })
                except:
                    continue 
    
    return pd.DataFrame(expanded_data)

# ---------------------------------------------------------
# 3. [핵심] 세로형 그래프 그리기 함수
# ---------------------------------------------------------
def draw_vertical_timetable(name1, df1, name2, df2):
    # 1행 2열 (왼쪽: 첫째, 오른쪽: 둘째)
    fig, axes = plt.subplots(1, 2, figsize=(14, 10), sharey=True) # Y축 공유
    
    targets = [(axes[0], name1, df1), (axes[1], name2, df2)]
    days_labels = ['월', '화', '수', '목', '금', '토', '일']
    
    # 공통 Y축 설정 (오전 8시 ~ 오후 10시) -> 위에서 아래로
    y_min, y_max = 8, 22 

    for ax, name, df in targets:
        # 배경 격자 (시간 기준 가로선)
        ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
        
        if not df.empty:
            # 세로 막대 그리기 (bar)
            # x: 요일, height: 소요시간, bottom: 시작시간
            bars = ax.bar(
                x=df['요일인덱스'], 
                height=df['소요시간'], 
                bottom=df['시작'], 
                color=df['색상'], 
                edgecolor='white', 
                width=0.8,
                zorder=3
            )

            # 텍스트 추가
            for i, bar in enumerate(bars):
                row = df.iloc[i]
                # 활동명
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 + 0.15, 
                        str(row['활동명']), 
                        ha='center', va='center', color='white', weight='bold', fontsize=10)
                # 시간
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 - 0.15, 
                        row['시간텍스트'], 
                        ha='center', va='center', color='white', fontsize=8)

        # 축 꾸미기
        ax.set_title(f"★ {name}", fontsize=18, weight='bold', pad=15)
        ax.set_xticks(range(7))
        ax.set_xticklabels(days_labels, fontsize=12, weight='bold')
        
        # Y축 반전 (시간이 위에서 아래로 흐르게)
        ax.set_ylim(y_max, y_min) 
        ax.set_yticks(range(y_min, y_max + 1))
        
        # 테두리 정리
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        # ax.spines['bottom'].set_visible(False)

    # 전체 제목
    plt.suptitle("📅 우리 아이 주간 통합 시간표", fontsize=22, weight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95]) # 제목 공간 확보
    
    return fig

# ---------------------------------------------------------
# 4. 초기 데이터 및 세션
# ---------------------------------------------------------
if 'data_1' not in st.session_state:
    st.session_state.data_1 = pd.DataFrame([
        {'활동명': '학교', '요일': '월,화,수,목,금', '시작시간': '09:00', '종료시간': '13:00', '색상': '#5D9CEC'},
        {'활동명': '학원', '요일': '월,수,금', '시작시간': '14:00', '종료시간': '16:00', '색상': '#FB6E52'},
        {'활동명': '축구', '요일': '토', '시작시간': '10:00', '종료시간': '12:00', '색상': '#48CFAD'},
    ])

if 'data_2' not in st.session_state:
    st.session_state.data_2 = pd.DataFrame([
        {'활동명': '유치원', '요일': '월,화,수,목,금', '시작시간': '09:30', '종료시간': '13:30', '색상': '#FFCE54'},
        {'활동명': '태권도', '요일': '화,목', '시작시간': '15:00', '종료시간': '16:00', '색상': '#AC92EC'},
        {'활동명': '낮잠', '요일': '토,일', '시작시간': '13:00', '종료시간': '15:00', '색상': '#AAB2BD'},
    ])

# ---------------------------------------------------------
# 5. 화면 UI
# ---------------------------------------------------------
st.title("📅 우리 아이 주간 통합 시간표 (세로형)")
st.markdown("X축은 요일, Y축은 시간(↓)입니다. 두 아이의 일정을 나란히 비교해보세요.")

# --- 입력 구역 (탭으로 분리) ---
tab1, tab2 = st.tabs(["📝 첫째 입력", "📝 둘째 입력"])

def render_input_area(key_suffix, data_key):
    st.info("💡 내용 수정 후 아래 [적용] 버튼을 눌러주세요.")
    temp_df = st.data_editor(
        st.session_state[data_key],
        column_config={
            "활동명": st.column_config.TextColumn("활동명", required=True),
            "요일": st.column_config.TextColumn("요일 (예: 월,수)", required=True),
            "시작시간": st.column_config.TextColumn("시작 (예: 14:00)", required=True),
            "종료시간": st.column_config.TextColumn("종료 (예: 15:00)", required=True),
            "색상": st.column_config.TextColumn("색상코드 (#)", default="#CCCCCC"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{key_suffix}"
    )
    return temp_df

with tab1:
    df1_temp = render_input_area("child1", "data_1")

with tab2:
    df2_temp = render_input_area("child2", "data_2")

# --- 통합 실행 버튼 ---
st.divider()
col_btn, col_view = st.columns([1, 4])

with col_btn:
    st.write("") # 여백
    st.write("") 
    if st.button("🔄 시간표 생성 및 적용", type="primary", use_container_width=True):
        st.session_state.data_1 = df1_temp
        st.session_state.data_2 = df2_temp
        st.rerun()

# --- 그래프 출력 구역 ---
with col_view:
    # 저장된 데이터 가져오기
    df1_final = process_data(st.session_state.data_1.astype(str))
    df2_final = process_data(st.session_state.data_2.astype(str))
    
    try:
        fig = draw_vertical_timetable("첫째(하민)", df1_final, "둘째(하율)", df2_final)
        st.pyplot(fig)
        
        # 다운로드 버튼
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
        st.download_button(
            label="💾 통합 시간표 이미지 저장",
            data=buf.getvalue(),
            file_name="family_timetable_vertical.png",
            mime="image/png",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"그래프 생성 중 오류가 발생했습니다: {e}")
