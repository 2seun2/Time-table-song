import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from io import BytesIO

# ---------------------------------------------------------
# 1. 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="우리 아이 시간표 꾸미기", layout="wide")

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
# 3. [핵심] 통합 그래프 그리기 (스타일 옵션 적용)
# ---------------------------------------------------------
def draw_merged_timetable(name1, icon1, df1, name2, icon2, df2, style_opts):
    # 그래프 크기 설정
    fig, ax = plt.subplots(figsize=(14, 10))
    
    days_labels = ['월', '화', '수', '목', '금']
    y_min, y_max = 8, 22
    
    # 스타일 옵션 가져오기
    title_size = style_opts['title_size']
    axis_size = style_opts['axis_size']
    bar_text_size = style_opts['bar_text_size']
    time_text_size = style_opts['time_text_size']
    font_weight = style_opts['font_weight']

    # -----------------------------------------------------
    # 배경 및 격자
    # -----------------------------------------------------
    ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)
    
    # 요일 구분선
    for x in range(len(days_labels) - 1):
        ax.axvline(x + 0.5, color='gray', linestyle='-', linewidth=1, alpha=0.3)
    
    # -----------------------------------------------------
    # 막대 그리기
    # -----------------------------------------------------
    bar_width = 0.4
    
    def plot_bars(df, offset):
        if df.empty: return
        
        x_positions = df['요일인덱스'] + offset
        
        bars = ax.bar(
            x=x_positions, 
            height=df['소요시간'], 
            bottom=df['시작'], 
            color=df['색상'], 
            edgecolor='white', 
            width=bar_width,
            zorder=3,
            alpha=0.9
        )
        
        for i, bar in enumerate(bars):
            row = df.iloc[i]
            # 활동명 (사용자 설정 크기/굵기 적용)
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 + 0.1, 
                    str(row['활동명']), 
                    ha='center', va='center', color='white', 
                    weight=font_weight, fontsize=bar_text_size)
            
            # 시간 텍스트 (너무 작으면 생략 가능하지만 일단 표시)
            if row['소요시간'] >= 0.5:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 - 0.2, 
                        row['시간텍스트'], 
                        ha='center', va='center', color='white', fontsize=time_text_size)

    # 첫째 그리기 (왼쪽)
    plot_bars(df1, -0.21)
    
    # 둘째 그리기 (오른쪽)
    plot_bars(df2, 0.21)

    # -----------------------------------------------------
    # 축 및 제목 설정
    # -----------------------------------------------------
    ax.set_xticks(range(5))
    ax.set_xticklabels(days_labels, fontsize=axis_size, weight=font_weight)
    
    # 상단 범례 (아이콘 포함)
    legend_text = f"◀ {icon1} {name1} (왼쪽)   |   {icon2} {name2} (오른쪽) ▶"
    ax.text(0, y_min - 0.6, legend_text, 
            fontsize=axis_size, weight='bold', color='#333333', ha='left',
            bbox=dict(facecolor='#f0f2f6', edgecolor='none', boxstyle='round,pad=0.5'))

    ax.set_ylim(y_max, y_min)
    ax.set_yticks(range(y_min, y_max + 1))
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plt.suptitle(f"{icon1} {icon2} 우리 아이 주간 시간표", fontsize=title_size, weight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    return fig

# ---------------------------------------------------------
# 4. 초기 데이터 (세션)
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
# 5. 화면 UI 구성
# ---------------------------------------------------------
st.title("🎨 우리 아이 시간표 만들기")

# --- [사이드바] 꾸미기 설정 ---
with st.sidebar:
    st.header("🎨 디자인 설정")
    
    st.subheader("1. 글자 크기/굵기")
    s_title_size = st.slider("제목 크기", 15, 40, 24)
    s_axis_size = st.slider("요일/범례 크기", 10, 25, 14)
    s_bar_text_size = st.slider("활동명(막대 안) 크기", 5, 20, 10)
    s_time_text_size = st.slider("시간(막대 안) 크기", 5, 15, 8)
    s_font_weight = st.radio("글자 굵기", ["bold", "normal"], index=0, horizontal=True)
    
    st.markdown("---")
    st.subheader("2. 아이 정보 입력")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        icon1 = st.selectbox("첫째 아이콘", ["🐶", "🐱", "🐰", "🐻", "🦖", "🚗", "👑", "🌈", "👦", "👧"], index=8)
    with col_s2:
        name1 = st.text_input("첫째 이름", value="하민")
        
    col_s3, col_s4 = st.columns(2)
    with col_s3:
        icon2 = st.selectbox("둘째 아이콘", ["🐥", "🐹", "🦊", "🐼", "🚀", "⚽", "⭐", "🍭", "👦", "👧"], index=9)
    with col_s4:
        name2 = st.text_input("둘째 이름", value="하율")
    
    st.info("👆 여기서 이름과 아이콘을 바꾸면 그래프에 반영됩니다.")

# 스타일 옵션 딕셔너리
style_options = {
    'title_size': s_title_size,
    'axis_size': s_axis_size,
    'bar_text_size': s_bar_text_size,
    'time_text_size': s_time_text_size,
    'font_weight': s_font_weight
}

# --- 메인 입력 구역 ---
st.markdown("### 📝 일정 입력")
tab1, tab2 = st.tabs([f"{icon1} {name1} 일정", f"{icon2} {name2} 일정"])

def render_input_area(key_suffix, data_key):
    temp_df = st.data_editor(
        st.session_state[data_key],
        column_config={
            "활동명": st.column_config.TextColumn("활동명", required=True),
            "요일": st.column_config.TextColumn("요일 (예: 월,수)", required=True),
            "시작시간": st.column_config.TextColumn("시작 (예: 14:00)", required=True),
            "종료시간": st.column_config.TextColumn("종료 (예: 15:00)", required=True),
            "색상": st.column_config.TextColumn("색상 (#)", default="#CCCCCC"),
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
col_btn, col_view = st.columns([1, 3])

with col_btn:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔄 그래프 업데이트", type="primary", use_container_width=True):
        st.session_state.data_1 = df1_temp
        st.session_state.data_2 = df2_temp
        st.rerun()

# --- 그래프 출력 ---
with col_view:
    df1_final = process_data(st.session_state.data_1.astype(str))
    df2_final = process_data(st.session_state.data_2.astype(str))
    
    try:
        fig = draw_merged_timetable(
            name1, icon1, df1_final, 
            name2, icon2, df2_final, 
            style_options
        )
        st.pyplot(fig)
        
        # 다운로드
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
        st.download_button(
            label=f"💾 {name1}&{name2} 시간표 저장",
            data=buf.getvalue(),
            file_name="cute_timetable.png",
            mime="image/png",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
