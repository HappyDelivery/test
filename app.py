import streamlit as st
import google.generativeai as genai
import os

# ==========================================
# 1. 페이지 설정 및 디자인
# ==========================================
st.set_page_config(
    page_title="PromptGenesis AI V8",
    page_icon="🧬",
    layout="wide"
)

st.markdown("""
<style>
    /* 다크 테마 & 가독성 */
    .stApp { background-color: #0e1117; color: #f0f2f6; }
    
    /* 입력 위젯 스타일 */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div, 
    .stMultiSelect > div > div > div {
        background-color: #262730; color: #ffffff; 
        border: 1px solid #4b5563; border-radius: 8px;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(90deg, #3a7bd5 0%, #3a6073 100%);
        color: white; border: none; font-weight: bold; height: 55px;
        font-size: 1.1rem; transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        transform: scale(1.02); box-shadow: 0 4px 15px rgba(58, 123, 213, 0.5);
    }
    
    /* 결과 박스 */
    .result-box {
        background-color: #1a1c24; padding: 20px;
        border-radius: 10px; border: 1px solid #333;
        font-family: 'Consolas', 'Courier New', monospace;
        line-height: 1.6; white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터: 템플릿 & 옵션
# ==========================================
TEMPLATES = {
    "✨ 직접 입력 (Custom)": {
        "personas": ["직접 입력"],
        "task": "",
        "default_context": []
    },
    "🛍️ 상품 상세페이지 카피": {
        "personas": ["10년차 이커머스 전문 카피라이터", "홈쇼핑 쇼호스트", "소비자 심리학 전문가"],
        "task": "고객의 구매 욕구를 자극하는 상품 상세페이지 도입부와 특징 설명(USP)을 작성하라.",
        "default_context": ["문제 제기(Pain Point) 후 해결책 제시", "모바일 가독성 최적화", "감성적인 스토리텔링"]
    },
    "📝 SEO 블로그 포스팅": {
        "personas": ["SEO 최적화 전문 마케터", "IT/테크 전문 파워 블로거", "논리적인 칼럼니스트"],
        "task": "검색 엔진 상위 노출을 노리는 정보성 블로그 글을 작성하라. (체류시간 증대 목적)",
        "default_context": ["소제목(H2, H3) 활용", "관련 키워드 5회 이상 반복", "결론에 요약 포함"]
    },
    "🎬 유튜브/숏츠 대본": {
        "personas": ["100만 구독자 유튜브 PD", "바이럴 마케팅 영상 기획자", "유머러스한 예능 작가"],
        "task": "초반 5초 안에 시청자를 사로잡는 훅(Hook)이 포함된 영상 스크립트를 작성하라.",
        "default_context": ["구어체 사용", "화면 전환/효과음 지시 포함", "시청자 참여 유도"]
    },
    "📧 비즈니스/영업 메일": {
        "personas": ["글로벌 B2B 세일즈 매니저", "고객 성공(CS) 팀장", "정중한 비서"],
        "task": "수신자가 거부감 없이 읽고, 회신을 보내고 싶게 만드는 비즈니스 메일을 작성하라.",
        "default_context": ["정중하지만 명확한 용건", "스팸성 표현 지양", "미팅 제안 포함"]
    },
    "💻 코드 생성 및 리뷰": {
        "personas": ["Google 수석 소프트웨어 엔지니어", "보안 전문 화이트 해커", "친절한 코딩 튜터"],
        "task": "요구사항을 만족하는 효율적이고 버그 없는 코드를 작성하고 설명을 덧붙여라.",
        "default_context": ["주석(Comment) 필수", "에러 처리(Try-Catch) 포함", "변수명 가독성 고려"]
    }
}

COMMON_OPTIONS = [
    "마크다운(Markdown) 형식", "표(Table) 포함", "글자 수 1000자 이상", 
    "이모지 적절히 사용", "초등학생도 이해하기 쉽게", "전문 용어 사용",
    "영어 번역 병기", "단계별(Step-by-step) 설명"
]

# ==========================================
# 3. 사이드바 구성 (심플 & 자동연결)
# ==========================================
with st.sidebar:
    if os.path.exists("character.png"):
        st.image("character.png", width=180)

    # [핵심] secrets.toml에서 키를 자동으로 가져옴
    # 사용자는 아무것도 입력할 필요가 없습니다.
    api_key = st.secrets.get("GOOGLE_API_KEY", None)

    # 만약 secrets.toml 파일이 없거나 키가 없으면 경고창 표시
    if not api_key:
        st.error("⚠️ `secrets.toml` 파일에 API Key가 없습니다.")
        st.info("새로 발급받은 키를 secrets.toml 파일에 저장해주세요.")
    
    # 모델 선택 (자동 감지)
    available_models = ["models/gemini-1.5-flash"] # 기본값
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            # 사용 가능한 모델 필터링 및 정렬
            model_list = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            model_list.sort(key=lambda x: 0 if 'flash' in x else 1) # Flash 우선
            if model_list:
                available_models = model_list
        except Exception:
            # 키가 틀렸거나 네트워크 문제 시 조용히 넘어감
            pass

    st.markdown("### ⚙️ 설정")
    selected_model = st.selectbox("AI 모델", available_models)
    temp = st.slider("창의성 (Temperature)", 0.0, 1.0, 0.7)

    st.divider()
    st.caption("PromptGenesis V8")

# ==========================================
# 4. 메인 UI 구성
# ==========================================
st.title("PromptGenesis AI")
st.markdown("##### 🚀 당신의 아이디어를 전문가급 프롬프트로 변환하세요.")

col_left, col_right = st.columns([1, 1], gap="large")

# --- [왼쪽] 입력 패널 ---
with col_left:
    st.subheader("🛠️ 설계도 작성")
    
    # 템플릿 선택
    cat_key = st.selectbox("📂 어떤 프롬프트를 만들까요?", list(TEMPLATES.keys()))
    current_data = TEMPLATES[cat_key]

    with st.container(border=True):
        # 페르소나
        persona_options = current_data["personas"] + ["직접 입력..."]
        selected_persona = st.selectbox("🎭 페르소나 (AI의 역할)", persona_options)
        
        if selected_persona == "직접 입력..." or cat_key == "✨ 직접 입력 (Custom)":
            final_persona = st.text_input("페르소나 직접 입력", value="")
        else:
            final_persona = selected_persona

        # Task
        task = st.text_area("🎯 핵심 과제 (AI가 할 일)", value=current_data["task"], height=100)
        
        # Context (멀티 선택)
        st.markdown("**📝 추가 조건 (선택)**")
        all_options = list(set(current_data["default_context"] + COMMON_OPTIONS))
        selected_options = st.multiselect("조건 선택", all_options, default=current_data["default_context"])
        
        additional_context = st.text_input("그 외 추가 내용", placeholder="예: 어조는 아주 정중하게...")

    generate_btn = st.button("✨ 슈퍼 프롬프트 생성", type="primary", use_container_width=True)

# --- [오른쪽] 결과 패널 ---
with col_right:
    st.subheader("💎 생성된 프롬프트")
    output_area = st.empty()

    if generate_btn:
        if not api_key:
            st.error("🚨 API Key 설정이 필요합니다. (secrets.toml 확인)")
        else:
            try:
                # 로딩 애니메이션
                output_area.markdown("""
                    <div style="text-align: center; padding: 50px;">
                        <img src="https://i.gifer.com/ZZ5H.gif" width="50">
                        <p style="color: #bbb;">최적화 중...</p>
                    </div>
                """, unsafe_allow_html=True)

                # 메타 프롬프트 구성
                context_str = ", ".join(selected_options)
                if additional_context:
                    context_str += f", {additional_context}"

                meta_prompt = f"""
                당신은 세계 최고의 '프롬프트 엔지니어'입니다.
                아래 요구사항을 분석하여 LLM에게 입력할 **최적의 시스템 프롬프트**를 작성해주세요.

                [입력 정보]
                - **Role:** {final_persona}
                - **Task:** {task}
                - **Constraints:** {context_str}

                [작성 규칙]
                1. 결과물은 복사하기 쉽게 **마크다운 코드 블록** 안에 작성하세요.
                2. [Role], [Task], [Context], [Tone] 등으로 섹션을 나누세요.
                3. 변수 처리가 필요한 부분은 {{변수}}로 표시하세요.
                """
                
                # API 호출
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model)
                
                response = model.generate_content(
                    meta_prompt,
                    generation_config={"temperature": temp}
                )
                
                output_area.markdown(response.text)
                st.toast("완료되었습니다!", icon="🎉")

            except Exception as e:
                # 에러 핸들링
                err_msg = str(e)
                if "403" in err_msg or "API key not valid" in err_msg:
                    output_area.error("🚨 **API Key 오류**")
                    st.error("설정된 API Key가 올바르지 않거나 차단되었습니다. secrets.toml을 확인하세요.")
                elif "429" in err_msg:
                    output_area.error("🚨 **사용량 초과**")
                    st.warning("잠시 후 다시 시도하거나, 사이드바에서 Flash 모델을 선택하세요.")
                else:
                    output_area.error(f"오류가 발생했습니다: {e}")
    else:
        output_area.info("왼쪽에서 내용을 입력하고 버튼을 눌러보세요.")
