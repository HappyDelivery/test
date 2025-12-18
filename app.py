import streamlit as st
import google.generativeai as genai
import os

# ==========================================
# 1. 화면 설정 (모바일 최적화)
# ==========================================
st.set_page_config(
    page_title="PromptGenesis Mobile",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 모바일 전용 CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #f0f2f6; }
    .block-container {
        padding-top: 2rem; padding-bottom: 3rem;
        padding-left: 1rem; padding-right: 1rem;
    }
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div {
        background-color: #262730; color: white; 
        border-radius: 12px; font-size: 16px;
    }
    .stButton > button {
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        color: white; border: none; font-weight: bold; 
        height: 60px; font-size: 1.2rem; border-radius: 15px;
        box-shadow: 0 4px 10px rgba(37, 117, 252, 0.3); width: 100%;
    }
    .streamlit-expanderHeader {
        background-color: #1f2937; border-radius: 10px;
        color: white; font-weight: bold;
    }
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap;
        background-color: #1f2937; border-radius: 10px;
        color: white; font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2575fc; color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터셋
# ==========================================
TEMPLATES = {
    "✨ 직접 입력 (Custom)": {"personas": ["직접 입력"], "task": "", "default_context": []},
    "🛍️ 상품 상세페이지": {
        "personas": ["이커머스 카피라이터", "홈쇼핑 쇼호스트", "심리학 전문가"],
        "task": "구매 욕구를 자극하는 상세페이지 도입부와 특징 설명(USP) 작성",
        "default_context": ["Pain Point 해결", "모바일 가독성", "감성 스토리"]
    },
    "📝 블로그 포스팅 (SEO)": {
        "personas": ["SEO 마케터", "파워 블로거", "IT 칼럼니스트"],
        "task": "검색 노출을 위한 정보성 블로그 글 작성 (체류시간 증대)",
        "default_context": ["소제목 활용", "키워드 5회 반복", "요약 포함"]
    },
    "🎬 유튜브/숏츠 대본": {
        "personas": ["유튜브 PD", "바이럴 기획자", "예능 작가"],
        "task": "초반 5초 훅(Hook)이 포함된 영상 스크립트 작성",
        "default_context": ["구어체", "화면 전환 지시", "구독 유도"]
    },
    "📧 비즈니스 메일": {
        "personas": ["B2B 세일즈", "CS 팀장", "비서"],
        "task": "정중하고 명확한 비즈니스 메일 작성",
        "default_context": ["정중한 어조", "명확한 용건", "미팅 제안"]
    },
    "💻 코드 생성/리뷰": {
        "personas": ["수석 개발자", "화이트 해커", "코딩 튜터"],
        "task": "효율적이고 버그 없는 코드 작성 및 설명",
        "default_context": ["주석 필수", "에러 처리", "가독성"]
    }
}

COMMON_OPTIONS = [
    "마크다운 형식", "표(Table) 포함", "글자 수 1000자 이상", 
    "이모지 사용", "쉽게 설명", "영어 번역 병기"
]

# ==========================================
# 3. 사이드바
# ==========================================
with st.sidebar:
    if os.path.exists("character.png"):
        st.image("character.png", width=150)
    
    st.header("⚙️ 설정")
    api_key = st.secrets.get("GOOGLE_API_KEY", None)
    
    available_models = ["models/gemini-1.5-flash"]
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            model_list = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            model_list.sort(key=lambda x: 0 if 'flash' in x else 1)
            if model_list: available_models = model_list
        except: pass
    
    selected_model = st.selectbox("AI 모델", available_models)
    temp = st.slider("창의성", 0.0, 1.0, 0.7)
    st.divider()
    st.caption("Mobile Edition V12")

# ==========================================
# 4. 메인 화면
# ==========================================

st.markdown("### 📱 PromptGenesis AI")
st.caption("터치 한 번으로 만드는 전문가 프롬프트")

# [1] 주제 선택
cat_key = st.selectbox("📂 주제를 선택하세요", list(TEMPLATES.keys()))
current_data = TEMPLATES[cat_key]

# [2] 할 일 입력
task = st.text_area("🎯 AI에게 시킬 일 (Task)", value=current_data["task"], height=100)

# [3] 언어 선택
lang_mode = st.radio(
    "🌐 출력 언어",
    ["🇰🇷 한글 전용", "🇺🇸 영어 전용", "🇰🇷 & 🇺🇸 듀얼 모드 (추천)"],
    index=2,
    horizontal=True
)

# [4] 세부 설정 (Expander)
with st.expander("🔽 세부 설정 (페르소나, 조건) 열기"):
    persona_options = current_data["personas"] + ["직접 입력..."]
    selected_persona = st.selectbox("🎭 역할 (Persona)", persona_options)
    if selected_persona == "직접 입력..." or cat_key == "✨ 직접 입력 (Custom)":
        final_persona = st.text_input("역할 직접 입력", value="")
    else:
        final_persona = selected_persona
        
    all_opts = list(set(current_data["default_context"] + COMMON_OPTIONS))
    selected_options = st.multiselect("📝 추가 조건", all_opts, default=current_data["default_context"])
    add_ctx = st.text_input("직접 추가할 조건", placeholder="예: 친절하게...")

# [5] 생성 버튼
if st.button("✨ 프롬프트 생성 (Touch)", use_container_width=True):
    if not api_key:
        st.error("설정(Secrets)에 API Key가 없습니다.")
    else:
        with st.container():
            with st.spinner("AI가 최적화 중입니다... 🔄"):
                try:
                    # [핵심 로직] 구분자(SPLIT)를 사용하여 두 버전을 분리 요청
                    split_token = "|||SPLIT|||"
                    
                    if "한글 전용" in lang_mode:
                        lang_inst = "프롬프트 전체를 유창한 '한국어'로 작성하세요."
                    elif "영어 전용" in lang_mode:
                        lang_inst = "Write the entire prompt in professional 'English'."
                    else:
                        lang_inst = (
                            f"두 가지 버전을 모두 작성하되, 두 버전 사이에 정확히 '{split_token}' 이라는 텍스트를 넣어 분리하세요.\n"
                            "1. 첫 번째: [한국어 버전] 프롬프트 작성\n"
                            f"2. {split_token} (구분자 출력)\n"
                            "3. 두 번째: [English Version] 프롬프트 작성"
                        )

                    ctx_str = ", ".join(selected_options)
                    if add_ctx: ctx_str += f", {add_ctx}"

                    meta_prompt = f"""
                    Role: Expert Prompt Engineer.
                    Task: Create a system prompt based on user inputs.
                    
                    [User Inputs]
                    - Role: {final_persona}
                    - Task: {task}
                    - Context: {ctx_str}
                    
                    [Output Rules]
                    1. Language Instruction: {lang_inst}
                    2. Format: Markdown Code Block.
                    3. Do NOT add extra explanations outside the code block.
                    """

                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(selected_model)
                    response = model.generate_content(meta_prompt, generation_config={"temperature": temp})
                    
                    # [결과 처리 로직]
                    full_text = response.text
                    st.success("✅ 생성 완료!")

                    # 듀얼 모드일 경우 탭으로 분리
                    if "듀얼 모드" in lang_mode and split_token in full_text:
                        parts = full_text.split(split_token)
                        tab1, tab2 = st.tabs(["🇰🇷 한국어 버전", "🇺🇸 English Version"])
                        
                        with tab1:
                            st.caption("우측 상단 아이콘을 누르면 복사됩니다.")
                            st.code(parts[0].strip(), language="markdown")
                            
                        with tab2:
                            st.caption("Copy button is on the top right.")
                            st.code(parts[1].strip(), language="markdown")
                    
                    # 단일 모드일 경우 그냥 출력
                    else:
                        st.caption("우측 상단 아이콘을 누르면 복사됩니다.")
                        st.code(full_text, language="markdown")
                    
                except Exception as e:
                    st.error(f"오류 발생: {e}")

st.write("")
st.write("")
