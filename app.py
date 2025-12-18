import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 페이지 설정 및 디자인 (CSS)
# ==========================================
st.set_page_config(
    page_title="PromptGenesis AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (스크린샷과 유사한 다크/네온 스타일 적용)
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {
        background-color: #050a14;
        color: #ffffff;
    }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > div {
        background-color: #0e1629;
        color: #ffffff;
        border: 1px solid #1f2a40;
        border-radius: 8px;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        height: 50px;
        width: 100%;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        opacity: 0.9;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
    }

    /* 헤더 스타일 */
    h1 {
        background: -webkit-linear-gradient(#60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    /* 상태 표시줄 (우측 상단 흉내) */
    .status-badge {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        border: 1px solid #059669;
        float: right;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 추천 시스템 데이터 (템플릿)
# ==========================================
# 사용자가 분야를 고르면 자동으로 채워질 내용들입니다.
TEMPLATES = {
    "직접 입력 (Custom)": {
        "persona": "",
        "task": "",
        "tone": "전문적인 (Professional)"
    },
    "공문서/보고서 작성": {
        "persona": "20년차 행정 전문가 및 기획자",
        "task": "다음 내용을 바탕으로 명확하고 격식 있는 공문서를 작성해주세요. 불필요한 미사여구는 빼고 핵심만 전달하세요.",
        "tone": "건조하고 명확한 (Dry & Clear)"
    },
    "블로그 글 작성 (SEO)": {
        "persona": "창의적인 파워 블로거 및 마케터",
        "task": "독자의 흥미를 끌 수 있는 매력적인 블로그 포스팅을 작성해주세요. 소제목을 잘 활용하고 이모지를 적절히 섞어주세요.",
        "tone": "친근하고 부드러운 (Friendly)"
    },
    "코드 생성 및 리팩토링": {
        "persona": "구글 출신 시니어 개발자",
        "task": "아래 요구사항을 만족하는 효율적이고 안전한 코드를 작성해주세요. 코드에는 주석으로 설명을 달아주세요.",
        "tone": "기술적인 (Technical)"
    },
    "비즈니스 이메일": {
        "persona": "글로벌 비즈니스 커뮤니케이션 전문가",
        "task": "상대방에게 정중하면서도 내 의도가 확실히 전달되도록 비즈니스 이메일 초안을 작성해주세요.",
        "tone": "정중한 (Polite)"
    }
}

# ==========================================
# 3. 로직 및 UI 구성
# ==========================================

# 상태 관리 초기화
if "result" not in st.session_state:
    st.session_state.result = ""

# API 키 설정 (사이드바)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712038.png", width=50)
    st.title("Settings")
    
    # [보안] 배포 시 st.secrets 사용 권장. 편의상 입력창 유지.
    api_key_input = st.text_input("Google API Key", value="AIzaSyBVxYQzLTs8uRP4yyJYS8yBDewLSm896Jg", type="password")
    
    model_name = st.selectbox("Model", ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"])
    temperature = st.slider("창의성 (Temperature)", 0.0, 1.0, 0.7)
    
    st.divider()
    st.markdown("Designed by **Expert AI Dev**")

# 메인 헤더
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("PromptGenesis AI")
    st.caption("당신의 아이디어를 실행 가능한 고품질 결과물로 진화시킵니다.")
with col_h2:
    st.markdown('<div class="status-badge">🟢 SYSTEM OPERATIONAL</div>', unsafe_allow_html=True)

st.write("") # 간격

# 메인 2단 레이아웃 (좌: 입력 / 우: 출력)
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.subheader("🟦 프롬프트 설계")
    
    # 1. 추천 기능 (템플릿 선택)
    selected_template = st.selectbox(
        "🚀 활용 분야 선택 (추천 템플릿 적용)", 
        list(TEMPLATES.keys())
    )
    
    # 선택된 템플릿 내용 가져오기
    current_template = TEMPLATES[selected_template]

    # 2. 입력 폼 (자동으로 채워짐)
    persona = st.text_input("🎭 페르소나 / 역할", value=current_template["persona"], placeholder="예: 20년차 마케팅 전문가")
    
    task = st.text_area("🎯 핵심 과제 (구체적 지시)", value=current_template["task"], height=150, placeholder="AI가 수행해야 할 구체적인 작업을 적어주세요.")
    
    context = st.text_area("📂 배경 자료 / 맥락", height=100, placeholder="참고할 데이터, 제약 조건, 행사 정보 등을 붙여넣으세요...")
    
    c1, c2 = st.columns(2)
    with c1:
        output_format = st.text_input("📝 출력 형식", placeholder="예: 마크다운, 표, 리스트")
    with c2:
        tone = st.selectbox("🗣️ 어조 (Tone)", ["전문적인", "친근한", "간결한", "감성적인"], index=0 if current_template["tone"] == "전문적인 (Professional)" else 1)

    # 생성 버튼
    generate_btn = st.button("✨ 결과 생성 (Generate)")

# 결과 생성 로직
if generate_btn:
    if not api_key_input:
        st.error("API Key를 입력해주세요.")
    else:
        try:
            # Gemini 설정
            genai.configure(api_key=api_key_input)
            model = genai.GenerativeModel(model_name)
            
            # 프롬프트 조합
            full_prompt = f"""
            [Role]: {persona}
            [Task]: {task}
            [Context]: {context}
            [Tone]: {tone}
            [Output Format]: {output_format}
            
            위 지시사항에 맞춰 최상의 답변을 작성해줘.
            """
            
            # 우측 패널에 로딩 표시
            with right_col:
                with st.spinner("AI가 최적화된 결과를 생성 중입니다..."):
                    response = model.generate_content(
                        full_prompt,
                        generation_config={"temperature": temperature}
                    )
                    st.session_state.result = response.text
        except Exception as e:
            st.error(f"에러 발생: {e}")

# 우측 패널 (출력)
with right_col:
    st.subheader("🟩 결과 확인")
    
    # 결과가 들어갈 컨테이너 스타일링
    result_container = st.container(border=True)
    with result_container:
        if st.session_state.result:
            st.markdown(st.session_state.result)
            st.markdown("---")
            st.caption("✅ 생성이 완료되었습니다. 내용을 복사하여 사용하세요.")
        else:
            # 대기 화면 (스크린샷의 로고 느낌)
            st.markdown(
                """
                <div style='text-align: center; color: #4b5563; padding: 100px 0;'>
                    <div style='font-size: 3rem;'>✨</div>
                    <h3>최적화 준비 완료</h3>
                    <p>왼쪽 패널에 정보를 입력하고 생성 버튼을 눌러주세요.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
