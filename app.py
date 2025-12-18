import streamlit as st
import google.generativeai as genai
import os

# ==========================================
# 1. 화면 설정 (모바일 최적화)
# ==========================================
st.set_page_config(
    page_title="PromptGenesis Mobile",
    page_icon="📱",
    layout="centered", # 모바일에서는 'wide'보다 'centered'가 앱처럼 보입니다.
    initial_sidebar_state="collapsed" # 모바일에서 사이드바는 처음에 닫혀있는게 좋습니다.
)

# 모바일 전용 CSS (여백 줄이기, 폰트 조정)
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #0e1117; color: #f0f2f6; }
    
    /* 헤더 여백 줄이기 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* 입력창 스타일 */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div {
        background-color: #262730; 
        color: white; 
        border-radius: 12px; /* 둥글게 */
        font-size: 16px; /* 모바일 가독성 */
    }

    /* 버튼 스타일 (크고 누르기 쉽게) */
    .stButton > button {
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        color: white; 
        border: none; 
        font-weight: bold; 
        height: 60px; /* 터치 영역 확보 */
        font-size: 1.2rem; 
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(37, 117, 252, 0.3);
        width: 100%;
    }
    .stButton > button:hover {
        opacity: 0.9;
    }

    /* 결과 박스 (카드 형태) */
    .result-box {
        background-color: #1a1c24; 
        padding: 15px;
        border-radius: 15px; 
        border: 1px solid #444;
        font-family: 'Consolas', monospace;
        font-size: 14px;
        line-height: 1.5; 
        white-space: pre-wrap;
        margin-top: 10px;
    }

    /* Expander (접이식 메뉴) 스타일 */
    .streamlit-expanderHeader {
        background-color: #1f2937;
        border-radius: 10px;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터셋 (템플릿)
# ==========================================
TEMPLATES = {
    "✨ 직접 입력 (Custom)": {
        "personas": ["직접 입력"], "task": "", "default_context": []
    },
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
# 3. 사이드바 (설정은 숨김)
# ==========================================
with st.sidebar:
    if os.path.exists("character.png"):
        st.image("character.png", width=150)
    
    st.header("⚙️ 설정")
    
    # Secrets에서 키 가져오기
    api_key = st.secrets.get("GOOGLE_API_KEY", None)
    if not api_key:
        st.error("Secrets 설정 필요")
    
    # 모델 선택
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
    st.caption("Mobile Edition V10")

# ==========================================
# 4. 메인 화면 (모바일 Flow)
# ==========================================

# 타이틀 (작고 깔끔하게)
st.markdown("### 📱 PromptGenesis AI")
st.caption("터치 한 번으로 만드는 전문가 프롬프트")

# [1] 핵심 선택 (가장 위에 노출)
cat_key = st.selectbox("📂 주제를 선택하세요", list(TEMPLATES.keys()))
current_data = TEMPLATES[cat_key]

# [2] 태스크 입력 (가장 중요하므로 항상 보임)
task = st.text_area("🎯 AI에게 시킬 일 (Task)", value=current_data["task"], height=100)

# [3] 언어 선택 (라디오 버튼)
lang_mode = st.radio(
    "🌐 출력 언어",
    ["🇰🇷 한글 전용", "🇺🇸 영어 전용", "🇰🇷+🇺🇸 한글+영어"],
    index=2, # 기본값: 한글+영어
    horizontal=True
)

# [4] 세부 설정 (접이식 - 모바일 공간 절약)
with st.expander("🔽 세부 설정 (페르소나, 조건) 열기"):
    # 페르소나
    persona_options = current_data["personas"] + ["직접 입력..."]
    selected_persona = st.selectbox("🎭 역할 (Persona)", persona_options)
    if selected_persona == "직접 입력..." or cat_key == "✨ 직접 입력 (Custom)":
        final_persona = st.text_input("역할 직접 입력", value="")
    else:
        final_persona = selected_persona
        
    # 옵션 선택
    all_opts = list(set(current_data["default_context"] + COMMON_OPTIONS))
    selected_options = st.multiselect("📝 추가 조건", all_opts, default=current_data["default_context"])
    add_ctx = st.text_input("직접 추가할 조건", placeholder="예: 친절하게...")

# [5] 생성 버튼 (크고 누르기 쉽게)
if st.button("✨ 프롬프트 생성 (Touch)", use_container_width=True):
    if not api_key:
        st.error("설정(Secrets)에 API Key가 없습니다.")
    else:
        result_container = st.container()
        
        # 로딩 표시
        with result_container:
            with st.spinner("AI가 최적화 중입니다... 🔄"):
                try:
                    # 언어 모드 설정
                    lang_inst = ""
                    if "한글 전용" in lang_mode: lang_inst = "한국어로 작성"
                    elif "영어 전용" in lang_mode: lang_inst = "Professional English"
                    else: lang_inst = "명령어는 영어, 설명은 한국어 병기"

                    # 조건 합치기
                    ctx_str = ", ".join(selected_options)
                    if add_ctx: ctx_str += f", {add_ctx}"

                    # 메타 프롬프트
                    meta_prompt = f"""
                    Role: Expert Prompt Engineer.
                    Task: Create a system prompt for an LLM based on user inputs.
                    
                    [User Inputs]
                    - Role: {final_persona}
                    - Task: {task}
                    - Context: {ctx_str}
                    - Language Mode: {lang_mode}
                    
                    [Rules]
                    1. Language Rule: {lang_inst}
                    2. Output in Markdown Code Block.
                    3. Sections: [Role], [Task], [Context], [Output Format].
                    """

                    # API 호출
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(selected_model)
                    response = model.generate_content(meta_prompt, generation_config={"temperature": temp})
                    
                    # 결과 출력
                    st.success("✅ 생성 완료!")
                    st.markdown(response.text)
                    st.caption("👆 위 코드를 복사해서 사용하세요.")
                    
                except Exception as e:
                    st.error(f"오류 발생: {e}")

# 하단 여백 확보
st.write("")
st.write("")
