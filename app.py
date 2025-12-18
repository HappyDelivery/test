import streamlit as st
import google.generativeai as genai
import os

# ==========================================
# 1. 페이지 설정 및 디자인
# ==========================================
st.set_page_config(
    page_title="PromptGenesis AI V7",
    page_icon="🛡️", # 보안 아이콘으로 변경
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
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        color: white; border: none; font-weight: bold; height: 55px;
        font-size: 1.1rem; transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        transform: scale(1.02); box-shadow: 0 4px 15px rgba(75, 108, 183, 0.5);
    }
    
    /* 결과 박스 & 에러 박스 */
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
        "default_context": ["문제 제기(Pain Point) 후 해결책 제시", "모바일 가독성 최적화"]
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
# 3. 함수: 모델 자동 감지
# ==========================================
def get_available_models(api_key):
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        model_list = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                model_list.append(m.name)
        # Flash 모델 우선 정렬
        model_list.sort(key=lambda x: 0 if 'flash' in x else (1 if 'pro' in x else 2))
        return model_list
    except Exception:
        return []

# ==========================================
# 4. 사이드바 구성 (보안 강화됨)
# ==========================================
with st.sidebar:
    # 캐릭터 표시
    if os.path.exists("character.png"):
        st.image("character.png", width=150)
    else:
        st.write("🦸‍♂️ Prompt Master")

    st.header("🔐 보안 설정")

    # 1. API Key 처리 (Secrets 우선 사용)
    # secrets.toml에 키가 있으면 자동으로 가져옵니다.
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ 안전한 저장소(Secrets)의 키를 사용 중입니다.")
    else:
        # 파일이 없으면 입력창 표시 (여전히 password 타입)
        api_key = st.text_input(
            "Google API Key 입력", 
            type="password", 
            placeholder="새로 발급받은 키를 입력하세요"
        )
        st.caption("Tip: `.streamlit/secrets.toml` 파일을 만들면 매번 입력하지 않아도 됩니다.")

    # 2. 모델 선택 (자동 감지)
    selected_model = None
    if api_key:
        available_models = get_available_models(api_key)
        if available_models:
            selected_model = st.selectbox("🤖 AI 모델 선택", available_models)
            if "flash" in selected_model:
                st.caption("⚡ 속도가 빠른 Flash 모델이 추천됩니다.")
        else:
            # 키가 유출되어 차단된 경우 등 에러 발생 시
            st.error("🚨 유효하지 않은 API Key입니다.")
            st.warning("Google AI Studio에서 '새 키'를 발급받으세요. 이전 키는 차단되었습니다.")
    
    temp = st.slider("창의성 (Temperature)", 0.0, 1.0, 0.7)
    st.divider()
    st.markdown("Developed by **20년차 개발자**")

# ==========================================
# 5. 메인 UI 구성
# ==========================================
st.title("PromptGenesis AI V7")
st.markdown("##### 🛡️ 보안이 강화된 전문가용 프롬프트 생성기")

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
        st.markdown("**📝 추가 조건 (클릭하여 선택)**")
        all_options = list(set(current_data["default_context"] + COMMON_OPTIONS))
        selected_options = st.multiselect("조건 선택", all_options, default=current_data["default_context"])
        
        additional_context = st.text_input("그 외 추가 내용", placeholder="예: 어조는 아주 정중하게...")

    generate_btn = st.button("✨ 슈퍼 프롬프트 생성 (Generate)", type="primary", use_container_width=True)

# --- [오른쪽] 결과 패널 ---
with col_right:
    st.subheader("💎 생성된 프롬프트")
    output_area = st.empty()

    if generate_btn:
        if not api_key:
            st.warning("👈 사이드바에 API Key를 입력하거나 secrets.toml을 설정하세요.")
        elif not selected_model:
            st.error("⚠️ 유효한 모델을 찾을 수 없습니다. API Key를 확인하세요.")
        else:
            try:
                # 로딩 애니메이션
                output_area.markdown("""
                    <div style="text-align: center; padding: 50px;">
                        <img src="https://i.gifer.com/ZZ5H.gif" width="50">
                        <p style="color: #bbb;">최적의 설계를 진행 중입니다...</p>
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
                1. 결과물은 **마크다운 코드 블록** 안에 작성하세요.
                2. [Role], [Task], [Context], [Tone] 등으로 섹션을 나누세요.
                3. 바로 복사해서 사용할 수 있도록 깔끔하게 출력하세요.
                """
                
                # API 호출
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model)
                
                response = model.generate_content(
                    meta_prompt,
                    generation_config={"temperature": temp}
                )
                
                output_area.markdown(response.text)
                st.toast("생성 완료!", icon="🎉")

            except Exception as e:
                # 403 에러 명시적 처리
                if "403" in str(e):
                    output_area.error("🚨 **API Key 차단됨 (403 Error)**")
                    st.error("Google이 해당 키를 유출된 것으로 판단하여 차단했습니다. 새 키를 발급받으세요.")
                else:
                    output_area.error(f"오류가 발생했습니다: {e}")
    else:
        output_area.info("왼쪽에서 옵션을 선택하고 버튼을 누르세요.")
