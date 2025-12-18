import streamlit as st
import google.generativeai as genai
import time
import os

# ==========================================
# 1. 페이지 설정 및 커스텀 디자인 (CSS)
# ==========================================
st.set_page_config(
    page_title="PromptGenesis AI - Master Edition",
    page_icon="🧬",
    layout="wide"
)

# 커스텀 CSS (로딩 애니메이션 & 디자인)
st.markdown("""
<style>
    /* 전체 배경: 다크 */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* 입력 필드 디자인 */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div {
        background-color: #262730; color: #ffffff; 
        border: 1px solid #4b5563; border-radius: 8px;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(90deg, #FF4B2B 0%, #FF416C 100%);
        color: white; border: none; font-weight: bold; height: 50px;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(255, 75, 43, 0.5);
    }
    
    /* 결과창 박스 스타일 */
    .result-box {
        background-color: #1e1e1e; padding: 25px;
        border-radius: 10px; border: 1px solid #444;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        font-family: 'Courier New', Courier, monospace; /* 코드 느낌 폰트 */
        white-space: pre-wrap; /* 줄바꿈 유지 */
    }

    /* 로딩 컨테이너 */
    .loading-container {
        text-align: center;
        padding: 50px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터셋: 프롬프트 생성용 템플릿
# ==========================================
# 여기서는 "AI가 수행할 작업"이 아니라 "AI에게 시킬 명령문"을 만드는 것이 목표입니다.
TEMPLATES = {
    "✨ 직접 입력 (Custom)": {"persona": "", "task": ""},
    "📝 블로그 글 작성 프롬프트": {
        "persona": "SEO 전문 마케터 및 파워 블로거",
        "task": "특정 키워드를 포함하여 검색 엔진 노출이 잘 되고, 체류 시간이 긴 매력적인 블로그 포스팅을 작성하게 하라."
    },
    "🎬 유튜브 대본 생성 프롬프트": {
        "persona": "100만 유튜버 PD 및 스토리텔러",
        "task": "시청자의 이탈을 막는 후킹(Hook) 멘트와 기승전결이 확실한 5분 분량의 영상 스크립트를 작성하게 하라."
    },
    "💻 코드 생성/리팩토링 프롬프트": {
        "persona": "Google 수석 엔지니어",
        "task": "제공된 요구사항에 맞춰 버그가 없고 효율적인 파이썬 코드를 작성하고, 각 라인에 대한 주석을 상세히 달게 하라."
    },
    "📧 콜드 메일(영업) 프롬프트": {
        "persona": "B2B 세일즈 전문가",
        "task": "잠재 고객의 거부감을 줄이고 미팅 성사율을 높일 수 있는 짧고 강력한 제안 메일을 작성하게 하라."
    },
    "🎨 이미지 생성(Midjourney) 프롬프트": {
        "persona": "전문 프롬프트 아티스트",
        "task": "Midjourney나 DALL-E에서 고퀄리티 이미지를 뽑아낼 수 있는 영어 프롬프트를 상세한 묘사(조명, 화풍, 렌즈 등)와 함께 작성하게 하라."
    }
}

# ==========================================
# 3. 사이드바 (설정 및 캐릭터)
# ==========================================
with st.sidebar:
    # 1. 캐릭터 이미지 배치 (파일이 있으면 표시)
    if os.path.exists("character.png"):
        st.image("character.png", width=200, caption="Prompt Gen Master")
    else:
        # 파일이 없을 경우 안내 문구
        st.info("💡 'character.png' 파일을 폴더에 넣으면 여기에 캐릭터가 표시됩니다.")
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712038.png", width=100)

    st.markdown("### ⚙️ 환경 설정")
    
    # 2. [보안] API Key 마스킹 처리 (type='password')
    api_key = st.text_input(
        "Google API Key", 
        value="AIzaSyBVxYQzLTs8uRP4yyJYS8yBDewLSm896Jg", 
        type="password", # 여기가 핵심! 이제 별표(*)로 보입니다.
        help="키는 안전하게 처리됩니다."
    )
    
    # 모델 자동 감지 및 선택
    available_models = ["gemini-1.5-flash"] # 기본값
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            detected = [m.name for m in models if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
            if detected: available_models = detected
        except:
            pass # 에러 시 기본값 사용
            
    selected_model = st.selectbox("AI 모델 선택", available_models)
    temperature = st.slider("창의성 (Creative Level)", 0.0, 1.0, 0.7)

    st.divider()
    st.markdown("Developed by **20년차 개발자 & AI 전문가**")

# ==========================================
# 4. 메인 UI (프롬프트 엔지니어링 도구)
# ==========================================

# 헤더 영역 (캐릭터와 타이틀)
c1, c2 = st.columns([1, 5])
with c1:
    if os.path.exists("character.png"):
        st.image("character.png", width=80)
    else:
        st.write("🤖")
with c2:
    st.title("PromptGenesis AI V4")
    st.caption("내가 원하는 결과를 얻기 위한 **'최적의 질문(Prompt)'**을 만들어주는 AI 도구입니다.")

st.markdown("---")

col_input, col_output = st.columns([1, 1], gap="large")

# --- [왼쪽] 입력 패널 ---
with col_input:
    st.subheader("🛠️ 설계도 작성")
    
    # 템플릿 선택
    cat_key = st.selectbox("어떤 프롬프트를 만들고 싶나요?", list(TEMPLATES.keys()))
    curr_tmpl = TEMPLATES[cat_key]

    # 입력 폼
    target_persona = st.text_input("🎭 AI에게 부여할 역할 (Persona)", value=curr_tmpl["persona"], placeholder="예: 20년차 개발자")
    target_task = st.text_area("🎯 AI가 수행해야 할 작업 (Task)", value=curr_tmpl["task"], height=100, placeholder="예: 블로그 글을 써라")
    
    user_context = st.text_area("📂 추가 제약 조건 / 포함할 내용", height=100, placeholder="예: 어조는 친절하게, 분량은 1000자 이상, 마크다운 형식 사용 등")

    # 생성 버튼
    generate_btn = st.button("🚀 슈퍼 프롬프트 생성 (Generate)", type="primary")

# --- [오른쪽] 결과 패널 ---
with col_output:
    st.subheader("💎 생성된 프롬프트 (복사해서 사용하세요)")
    
    output_container = st.empty()

    if generate_btn:
        if not api_key:
            st.error("API Key를 입력해주세요.")
        else:
            try:
                # 1. 로딩 애니메이션 (움직이는 이미지)
                # Streamlit은 GIF를 지원합니다. 로딩 중일 때 표시할 GIF URL입니다.
                loading_gif = "https://i.gifer.com/ZZ5H.gif" # DNA/Brain 로딩 같은 느낌
                
                output_container.markdown(f"""
                    <div class="loading-container">
                        <img src="{loading_gif}" width="100">
                        <p style="margin-top:10px; font-weight:bold; color:#aaa;">
                            최적의 프롬프트를 설계하는 중입니다...<br>
                            (Prompt Engineering in progress)
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                # 2. 메타 프롬프트 (AI에게 프롬프트를 짜달라고 시키는 프롬프트)
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model)
                
                meta_prompt = f"""
                당신은 세계 최고의 '프롬프트 엔지니어'입니다.
                사용자의 요구사항을 분석하여, LLM(Chatgpt, Gemini, Claude 등)에게 입력했을 때 최고의 성능을 낼 수 있는 **'시스템 프롬프트(System Prompt)'**를 작성해주세요.
                
                [사용자 요구사항]
                - AI 역할: {target_persona}
                - 수행 작업: {target_task}
                - 제약/맥락: {user_context}
                
                [작성 규칙]
                1. 프롬프트는 전문적이고 구조화된 형식(마크다운)으로 작성하세요.
                2. [Role], [Task], [Constraints], [Output Format], [Tone] 등의 섹션을 나누세요.
                3. 변수 처리가 필요한 곳은 {{변수명}} 형태로 표시하세요.
                4. 결과물은 바로 복사해서 사용할 수 있는 '코드 블록' 안에 넣어서 출력하세요.
                5. 언어는 한국어로 작성하되, 필요하다면 영어 프롬프트를 추가로 제안하세요.
                """
                
                # 3. AI 응답 생성
                response = model.generate_content(
                    meta_prompt,
                    generation_config={"temperature": temperature}
                )
                
                # 4. 결과 출력
                output_container.markdown(response.text)
                st.success("✅ 생성이 완료되었습니다! 위 내용을 복사해서 AI에게 붙여넣으세요.")

            except Exception as e:
                output_container.error(f"오류가 발생했습니다: {e}")
                
    else:
        # 대기 화면
        output_container.markdown("""
        <div style='text-align: center; color: #6b7280; padding: 100px 0; border: 2px dashed #374151; border-radius: 10px;'>
            <h3>👋 준비 완료</h3>
            <p>왼쪽에서 설정을 마치고<br> <b>[슈퍼 프롬프트 생성]</b> 버튼을 눌러주세요.</p>
        </div>
        """, unsafe_allow_html=True)
