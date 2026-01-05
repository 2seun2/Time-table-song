import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from io import BytesIO

# ---------------------------------------------------------
# 1. 기본 설정
# ---------------------------------------------------------
st.set_page_config(page_title="우리 아이 시간표 (저장기능 포함)", layout="wide")

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
# 2. 데이터 처리 및 유틸리티
# ---------------------------------------------------------
def convert_df_to_csv(df):
    # 엑셀에서 한글 깨짐 방지를 위해 'utf-8-sig' 사용
    return df.to_csv(index=False).encode('utf-8-sig')

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
# 3. 그래프 그리기
# ---------------------------------------------------------
def draw_merged_timetable(name1, icon1, df1, name2, icon2, df2, style_opts):
    fig, ax = plt.subplots(figsize=(14, 10))
    days_labels = ['월', '화', '수', '목', '금']
    y_min, y_max = 8, 22
    
    # 스타일 적용
    title_size = style_opts['title_size']
    axis_size = style_opts['axis_size']
    bar_text_size = style_opts['bar_text_size']
    time_text_size = style_opts['time_text_size']
    font_weight = style_opts['font_weight']

    ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)
    for x in range(len(days_labels) - 1):
        ax.axvline(x + 0.5, color='gray', linestyle='-', linewidth=1, alpha=0.3)
    
    bar_width = 0.4
    
    def plot_bars(df, offset):
        if df.empty: return
        x_positions = df['요일인덱스'] + offset
        bars = ax.bar(x=x_positions, height=df['소요시간'], bottom=df['시작'], 
                      color=df['색상'], edgecolor='white', width=bar_width, zorder=3, alpha=0.9)
        
        for i, bar in enumerate(bars):
            row = df.iloc[i]
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 + 0.1, 
                    str(row['활동명']), ha='center', va='center', color='white', 
                    weight=font_weight, fontsize=bar_text_size)
            if row['소요시간'] >= 0.5:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2 - 0.2, 
                        row['시간텍스트'], ha='center', va='center', color='white', fontsize=time_text_size)

    plot_bars(df1, -0.21)
    plot_bars(df2, 0.21)

    ax.set_xticks(range(5))
    ax.set_xticklabels(days_labels, fontsize=axis_size, weight=font_weight)
    
    legend_text = f"◀ {icon1} {name1} (왼쪽)   |   {icon2} {name2} (오른쪽) ▶"
    ax.text(0, y_min - 0.6, legend_text, fontsize=axis_size, weight='bold', color='#333333', ha='left',
            bbox=dict(facecolor='#f0f2f6', edgecolor='none', boxstyle='round,pad=0.5'))

    ax.set_ylim(y_max, y_min)
    ax.set_yticks(range(y_min, y_max + 1))
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['left'].set_visible(False)

    plt.suptitle(f"{icon1} {icon2} 우리 아이 주간 시간표", fontsize=title_size, weight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig

# ---------------------------------------------------------
# 4. 초기 데이터 및 화면 구성
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

st.title("💾 우리 아이 시간표 (파일 저장/불러오기)")

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("🎨 디자인 설정")
    s_title_size = st.slider("제목 크기", 15, 40, 24)
    s_axis_size = st.slider("요일/범례 크기", 10, 25, 14)
    s_bar_text_size = st.slider("활동명 글자 크기", 5, 20, 10)
    s_time_text_size = st.slider("시간 글자 크기", 5, 15, 8)
    s_font_weight = st.radio("글자 굵기", ["bold", "normal"], index=0, horizontal=True)
    
    st.markdown("---")
    st.subheader("아이 정보")
    col_s1, col_s2 = st.columns(2)
    with col_s1: icon1 = st.selectbox("첫째 아이콘", ["🐶", "🐱", "🐰", "👦"], index=0)
    with col_s2: name1 = st.text_input("첫째 이름", value="하민")
    col_s3, col_s4 = st.columns(2)
    with col_s3: icon2 = st.selectbox("둘째 아이콘", ["🐥", "🐹", "🦊", "👧"], index=3)
    with col_s4: name2 = st.text_input("둘째 이름", value="하율")

style_options = {'title_size': s_title_size, 'axis_size': s_axis_size, 
                 'bar_text_size': s_bar_text_size, 'time_text_size': s_time_text_size, 'font_weight': s_font_weight}

# --- 메인 탭 ---
tab1, tab2 = st.tabs([f"{icon1} {name1} 데이터 관리", f"{icon2} {name2} 데이터 관리"])

def manage_child_data(key_suffix, data_key, child_name):
    col_edit, col_file = st.columns([3, 1])
    
    with col_file:
        st.info("📂 **불러오기**")
        uploaded_file = st.file_uploader("저장된 파일(CSV) 업로드", type=['csv'], key=f"upload_{key_suffix}")
        
        if uploaded_file is not None:
            try:
                # 파일 읽기 및 세션 업데이트
                uploaded_df = pd.read_csv(uploaded_file)
                st.session_state[data_key] = uploaded_df
                st.success("로드 완료! (자동 적용됨)")
            except Exception as e:
                st.error("파일 형식 오류")

    with col_edit:
        st.subheader(f"📝 {child_name} 일정 편집")
        # 데이터 에디터
        edited_df = st.data_editor(
            st.session_state[data_key],
            column_config={
                "활동명": st.column_config.TextColumn("활동명", required=True),
                "요일": st.column_config.TextColumn("요일", required=True),
                "시작시간": st.column_config.TextColumn("시작", required=True),
                "종료시간": st.column_config.TextColumn("종료", required=True),
                "색상": st.column_config.TextColumn("색상", default="#CCCCCC"),
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{key_suffix}"
        )
        
        # 수정사항 즉시 반영을 위한 임시 저장
        if not edited_df.equals(st.session_state[data_key]):
             st.session_state[data_key] = edited_df
             st.rerun()

    # 데이터 다운로드 버튼 (아래 배치)
    st.write("")
    csv = convert_df_to_csv(edited_df)
    st.download_button(
        label=f"💾 {child_name} 데이터 파일(CSV) 저장하기",
        data=csv,
        file_name=f"{child_name}_schedule_data.csv",
        mime='text/csv',
        key=f"download_{key_suffix}",
        help="이 파일을 저장해두면 나중에 다시 불러올 수 있습니다."
    )

with tab1:
    manage_child_data("child1", "data_1", name1)

with tab2:
    manage_child_data("child2", "data_2", name2)

# --- 그래프 출력 ---
st.divider()
st.subheader("📊 통합 시간표 미리보기")

df1_final = process_data(st.session_state.data_1.astype(str))
df2_final = process_data(st.session_state.data_2.astype(str))

try:
    fig = draw_merged_timetable(name1, icon1, df1_final, name2, icon2, df2_final, style_options)
    st.pyplot(fig)
    
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
    st.download_button(
        label="🖼️ 완성된 시간표 이미지 다운로드",
        data=buf.getvalue(),
        file_name="final_timetable.png",
        mime="image/png",
        type="primary"
    )
except Exception as e:
    st.error(f"그래프 오류: {e}")
