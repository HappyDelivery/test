import streamlit as st
import google.generativeai as genai
import os

# ==========================================
# 1. 페이지 설정 및 디자인
# ==========================================
st.set_page_config(
    page_title="PromptGenesis AI V6",
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
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; font-weight: bold; height: 55px;
        font-size: 1.1rem; transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        transform: scale(1.02); box-shadow: 0 4px 15px rgba(118, 75, 162, 0.5);
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
# 2. 데이터: 템플릿 & 추천 페르소나/옵션
# ==========================================
TEMPLATES = {
    "🛍️ 상품 상세페이지 카피": {
        "personas": [
            "10년차 이커머스 전문 카피라이터",
            "홈쇼핑 쇼호스트 출신 기획자",
            "소비자 심리학 전문가",
            "감성적인 브랜드 에디터"
        ],
        "task": "고객의 구매 욕구를 자극하는 상품 상세페이지 도입부와 특징 설명(USP)을 작성하라.",
        "default_context": ["문제 제기(Pain Point) 후 해결책 제시", "모바일 가독성 최적화"]
    },
    "📝 SEO 블로그 포스팅": {
        "personas": [
            "SEO 최적화 전문 마케터",
            "IT/테크 전문 파워 블로거",
            "친근한 옆집 언니 같은 리뷰어",
            "논리적이고 분석적인 칼럼니스트"
        ],
        "task": "검색 엔진 상위 노출을 노리는 정보성 블로그 글을 작성하라. (체류시간 증대 목적)",
        "default_context": ["소제목(H2, H3) 활용", "관련 키워드 5회 이상 반복", "결론에 요약 포함"]
    },
    "🎬 유튜브/숏츠 대본": {
        "personas": [
            "100만 구독자 유튜브 PD",
            "바이럴 마케팅 영상 기획자",
            "유머러스한 예능 작가",
            "신뢰감을 주는 뉴스 앵커"
        ],
        "task": "초반 5초 안에 시청자를 사로잡는 훅(Hook)이 포함된 영상 스크립트를 작성하라.",
        "default_context": ["구어체 사용", "화면 전환/효과음 지시 포함", "시청자 참여 유도(댓글, 구독)"]
    },
    "📧 비즈니스/영업 메일": {
        "personas": [
            "글로벌 B2B 세일즈 매니저",
            "스타트업 CEO",
            "고객 성공(CS) 팀장",
            "정중한 비서"
        ],
        "task": "수신자가 거부감 없이 읽고, 회신을 보내고 싶게 만드는 비즈니스 메일을 작성하라.",
        "default_context": ["정중하지만 명확한 용건", "스팸성 표현 지양", "미팅 제안 포함"]
    },
    "💻 코드 생성 및 리뷰": {
        "personas": [
            "Google 수석 소프트웨어 엔지니어",
            "보안 전문 화이트 해커",
            "친절한 코딩 튜터",
            "데이터 사이언티스트"
        ],
        "task": "요구사항을 만족하는 효율적이고 버그 없는 코드를 작성하고 설명을 덧붙여라.",
        "default_context": ["주석(Comment) 필수", "에러 처리(Try-Catch) 포함", "변수명 가독성 고려"]
    },
    "🎨 미드저니/이미지 프롬프트": {
        "personas": [
            "AI 아트 디렉터",
            "전문 사진작가 (Photographer)",
            "영화 컨셉 아티스트",
            "3D 렌더링 전문가"
        ],
        "task": "고품질 이미지를 생성하기 위한 상세한 영어 프롬프트를 작성하라.",
        "default_context": ["조명(Lighting) 묘사", "카메라 렌즈/각도 설정", "스타일(화풍) 지정"]
    },
    "✨ 직접 입력 (Custom)": {
        "personas": ["직접 입력"],
        "task": "",
        "default_context": []
    }
}

# 자주 쓰는 옵션들 (체크박스용)
COMMON_OPTIONS = [
    "마크다운(Markdown) 형식", "표(Table) 포함", "글자 수 1000자 이상", 
    "이모지 적절히 사용", "초등학생도 이해하기 쉽게", "전문 용어 사용",
    "영어 번역 병기", "단계별(Step-by-step) 설명"
]

# ==========================================
# 3. 함수: 모델 자동 감지 (에러 해결의 핵심)
# ==========================================
def get_available_models(api_key):
    """API 키로 사용 가능한 모델 리스트를 가져오고, Flash 모델을 최우선으로 정렬함"""
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        model_list = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                model_list.append(m.name)
        
        # 정렬 로직: 'flash'가 들어간 모델을 리스트 맨 앞으로 보냄 (가성비/속도)
        model_list.sort(key=lambda x: 0 if 'flash' in x else (1 if 'pro' in x else 2))
        return model_list
    except Exception:
        return []

# ==========================================
# 4. 사이드바 구성
# ==========================================
with st.sidebar:
    # 캐릭터 (파일 있으면 표시)
    if os.path.exists("character.png"):
        st.image("character.png", width=150)
    else:
        st.write("🦸‍♂️ Prompt Master")

    st.header("⚙️ 설정 (Settings)")
    
    # [보안] API Key 입력 (비밀번호 모드)
    # Streamlit Cloud 배포 시 st.secrets를 쓰면 자동으로 불러옵니다.
    default_key = st.secrets.get("GOOGLE_API_KEY", "")
    api_key = st.text_input(
        "Google API Key", 
        value=default_key, 
        type="password", 
        placeholder="AIza... 키를 입력하세요"
    )

    # 모델 선택 (자동 감지)
    if api_key:
        available_models = get_available_models(api_key)
        if available_models:
            # 성공적으로 가져옴
            selected_model = st.selectbox("🤖 AI 모델 선택 (자동 감지됨)", available_models)
            if "flash" in selected_model:
                st.caption("✅ 추천: 속도가 빠르고 무료 사용량이 넉넉한 Flash 모델입니다.")
        else:
            # 키는 넣었지만 목록 로드 실패 시 (안전장치)
            st.warning("모델 목록을 불러오지 못했습니다. 키를 확인하세요.")
            selected_model = "models/gemini-1.5-flash-latest" # 강제 기본값
    else:
        st.info("API Key를 입력하면 모델 목록이 나타납니다.")
        selected_model = None

    temp = st.slider("창의성 (Temperature)", 0.0, 1.0, 0.7)
    
    st.divider()
    st.markdown("Developed by **20년차 개발자**")

# ==========================================
# 5. 메인 UI 구성
# ==========================================
st.title("PromptGenesis AI V6")
st.markdown("##### 🚀 당신의 아이디어를 '최고의 프롬프트'로 바꿔주는 생성기")

col_left, col_right = st.columns([1, 1], gap="large")

# --- [왼쪽] 입력 패널 ---
with col_left:
    st.subheader("🛠️ 설계도 작성")
    
    # 1. 템플릿 선택
    cat_key = st.selectbox("📂 어떤 프롬프트를 만들까요?", list(TEMPLATES.keys()))
    current_data = TEMPLATES[cat_key]

    with st.container(border=True):
        # 2. 페르소나 선택 (추천 리스트)
        persona_options = current_data["personas"] + ["직접 입력..."]
        selected_persona = st.selectbox("🎭 페르소나 (AI의 역할)", persona_options)
        
        # 직접 입력 선택 시 텍스트 입력창 활성화
        if selected_persona == "직접 입력..." or cat_key == "✨ 직접 입력 (Custom)":
            final_persona = st.text_input("페르소나를 직접 입력하세요", value="")
        else:
            final_persona = selected_persona

        # 3. Task (수정 가능)
        task = st.text_area("🎯 핵심 과제 (AI가 할 일)", value=current_data["task"], height=100)
        
        # 4. Context (멀티 선택 + 추가 입력)
        st.markdown("**📝 추가 조건 (클릭하여 선택)**")
        
        # 템플릿별 추천 옵션 + 공통 옵션 합치기
        all_options = list(set(current_data["default_context"] + COMMON_OPTIONS))
        selected_options = st.multiselect("조건 선택", all_options, default=current_data["default_context"])
        
        # 추가 텍스트 입력
        additional_context = st.text_input("그 외 추가할 내용이 있다면?", placeholder="예: 어조는 아주 정중하게...")

    generate_btn = st.button("✨ 슈퍼 프롬프트 생성 (Generate)", type="primary", use_container_width=True)

# --- [오른쪽] 결과 패널 ---
with col_right:
    st.subheader("💎 생성된 프롬프트")
    output_area = st.empty()

    if generate_btn:
        if not api_key:
            st.error("🔒 사이드바에 **Google API Key**를 입력해주세요.")
        elif not selected_model:
            st.error("⚠️ 모델을 선택해주세요.")
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
                # 사용자가 선택한 옵션들을 문자열로 합침
                context_str = ", ".join(selected_options)
                if additional_context:
                    context_str += f", {additional_context}"

                meta_prompt = f"""
                당신은 세계 최고의 '프롬프트 엔지니어'입니다.
                아래 요구사항을 분석하여 LLM(ChatGPT, Gemini 등)에게 입력할 **최적의 시스템 프롬프트**를 작성해주세요.

                [입력 정보]
                - **Role(역할):** {final_persona}
                - **Task(작업):** {task}
                - **Constraints(제약조건):** {context_str}

                [작성 규칙]
                1. 결과물은 **마크다운 코드 블록** 안에 작성하여 바로 복사할 수 있게 하세요.
                2. [Role], [Task], [Context], [Tone], [Output Format] 등 구조적으로 섹션을 나누세요.
                3. 한국어로 작성하되, 필요시 영어 명령어를 병기하세요.
                """
                
                # API 호출
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model)
                
                response = model.generate_content(
                    meta_prompt,
                    generation_config={"temperature": temp}
                )
                
                # 결과 출력
                output_area.markdown(response.text)
                st.toast("생성 완료! 복사해서 사용하세요.", icon="🎉")

            except Exception as e:
                output_area.error(f"오류가 발생했습니다: {e}")
                # 혹시라도 모델 이름 에러가 나면 힌트 제공
                if "404" in str(e):
                    st.warning("선택하신 모델이 현재 지역이나 계정에서 지원되지 않을 수 있습니다. 사이드바에서 다른 모델을 선택해보세요.")

    else:
        # 대기 화면
        output_area.info("왼쪽에서 옵션을 선택하고 버튼을 누르세요. \n전문가 수준의 프롬프트가 생성됩니다.")
