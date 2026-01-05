import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from io import BytesIO

# ---------------------------------------------------------
# 1. 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="평일 통합 시간표", layout="wide")

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
# 2. 데이터 처리 함수 (토/일 자동 제외)
# ---------------------------------------------------------
def process_data(df):
    """ 데이터프레임을 그래프용 수치 데이터로 변환 """
    expanded_data = []
    # 토, 일 제외한 요일 정의
    day_order = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4}
    
    for index, row in df.iterrows():
        days_str = str(row.get('요일', '')).strip()
        start_str = str(row.get('시작시간', '')).strip()
        end_str = str(row.get('종료시간', '')).strip()
        activity_str = str(row.get('활동명', '')).strip()

        if not days_str or not start_str or not end_str or ':' not in start_str:
            continue

        days = days_str.split(',')
        
        for day in days:
            day = day.strip()
            # 주말(토,일)이거나 오타면 건너뜀
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
                        '시작': start_float,
                        '소요시간': end_float - start_float,
                        '색상': color_val,
                        '시간텍스트': f"{start_str}~{end_str}"
                    })
                except:
                    continue 
    
    return pd.DataFrame(expanded_data)

# ---------------------------------------------------------
# 3. [핵심] 한 표에 반반 나누어 그리기
# ---------------------------------------------------------
def draw_merged_timetable(name1, df1, name2, df2):
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 요일 설정 (월~금)
    days_labels = ['월', '화', '수', '목', '금']
    
    # Y축 범위 (오전 8시 ~ 오후 10시)
    y_min, y_max = 8, 22
    
    # -----------------------------------------------------
    # 배경 및 격자 꾸미기
    # -----------------------------------------------------
    # 가로선 (시간)
    ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)
    
    # 세로선 (요일 구분선) - 중요!
    # 0.5, 1.5, 2.5 위치에 선을 그어 요일을 명확히 구분
    for x in range(len(days_labels) - 1):
        ax.axvline(x + 0.5, color='gray', linestyle='-', linewidth=1, alpha=0.3)
    
    # -----------------------------------------------------
    # 그래프 그리기 로직 (반반 나누기)
    # -----------------------------------------------------
    bar_width = 0.4 # 막대 너비 (0.5보다 작아야 안 겹침)
    
    # 함수: 특정 아이의 막대 그리기 (offset: 위치 이동)
    def plot_bars(df, offset, is_left):
        if df.empty: return
        
        # X축 위치 조정 (왼쪽 아이는 -0.2, 오른쪽 아이는 +0.2)
        x_positions = df['요일인덱스'] + offset
        
        bars = ax.bar(
            x=x_positions, 
            height=df['소요시간'], 
            bottom=df['시작'], 
            color=df['색상'], 
            edgecolor='white', 
            width=bar_width,
            zorder=3,
            alpha=0.9 # 약간 투명하게 해서 겹쳐보이는 느낌 방지
        )
        
        # 텍스트 추가
        for i, bar in enumerate(bars):
            row = df.iloc[i]
            # 공간이 좁으므로 글자 크기 조절
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 + 0.1, 
                    str(row['활동명']), 
                    ha='center', va='center', color='white', weight='bold', fontsize=9)
            
            # 시간이 너무 짧으면(1시간 미만) 시간 텍스트 생략 가능
            if row['소요시간'] >= 0.5:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 - 0.2, 
                        row['시간텍스트'], 
                        ha='center', va='center', color='white', fontsize=7)

    # 첫째 그리기 (왼쪽: -0.21 위치)
    plot_bars(df1, -0.21, True)
    
    # 둘째 그리기 (오른쪽: +0.21 위치)
    plot_bars(df2, 0.21, False)

    # -----------------------------------------------------
    # 축 설정
    # -----------------------------------------------------
    ax.set_xticks(range(5))
    
    # X축 라벨을 조금 더 예쁘게 (아이 이름 표시)
    new_labels = []
    for day in days_labels:
        new_labels.append(f"{day}")
        
    ax.set_xticklabels(new_labels, fontsize=14, weight='bold')
    
    # 상단에 범례(누가 왼쪽인지) 표시
    ax.text(0, y_min - 0.5, f"◀ {name1} (왼쪽)  |  {name2} (오른쪽) ▶", 
            fontsize=12, weight='bold', color='#333333', ha='left',
            bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5'))

    # Y축 반전 및 설정
    ax.set_ylim(y_max, y_min)
    ax.set_yticks(range(y_min, y_max + 1))
    
    # 테두리 정리
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plt.suptitle("📅 평일 스케줄 통합 비교 (월~금)", fontsize=22, weight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    return fig

# ---------------------------------------------------------
# 4. 초기 데이터 및 세션
# ---------------------------------------------------------
if 'data_1' not in st.session_state:
    st.session_state.data_1 = pd.DataFrame([
        {'활동명': '학교', '요일': '월,화,수,목,금', '시작시간': '09:00', '종료시간': '13:00', '색상': '#5D9CEC'},
        {'활동명': '학원', '요일': '월,수,금', '시작시간': '14:00', '종료시간': '16:00', '색상': '#FB6E52'},
    ])

if 'data_2' not in st.session_state:
    st.session_state.data_2 = pd.DataFrame([
        {'활동명': '유치원', '요일': '월,화,수,목,금', '시작시간': '09:30', '종료시간': '13:30', '색상': '#FFCE54'},
        {'활동명': '태권도', '요일': '화,목', '시작시간': '15:00', '종료시간': '16:00', '색상': '#AC92EC'},
    ])

# ---------------------------------------------------------
# 5. 화면 UI
# ---------------------------------------------------------
st.title("📅 평일 통합 시간표 (월~금)")
st.markdown("""
- **왼쪽 반:** 첫째 아이 일정
- **오른쪽 반:** 둘째 아이 일정
- **토/일요일:** 자동으로 제외됩니다.
""")

# --- 입력 구역 ---
tab1, tab2 = st.tabs(["📝 첫째 입력", "📝 둘째 입력"])

def render_input_area(key_suffix, data_key):
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

# --- 실행 버튼 ---
st.divider()
col_btn, col_view = st.columns([1, 4])

with col_btn:
    st.write("") 
    st.write("") 
    if st.button("🔄 시간표 생성 및 적용", type="primary", use_container_width=True):
        st.session_state.data_1 = df1_temp
        st.session_state.data_2 = df2_temp
        st.rerun()

# --- 그래프 출력 구역 ---
with col_view:
    df1_final = process_data(st.session_state.data_1.astype(str))
    df2_final = process_data(st.session_state.data_2.astype(str))
    
    try:
        # 통합 그래프 그리기 호출
        fig = draw_merged_timetable("첫째(좌)", df1_final, "둘째(우)", df2_final)
        st.pyplot(fig)
        
        # 다운로드 버튼
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
        st.download_button(
            label="💾 통합 시간표 저장",
            data=buf.getvalue(),
            file_name="merged_timetable_weekday.png",
            mime="image/png",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
