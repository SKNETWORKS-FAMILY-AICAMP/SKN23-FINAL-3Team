/**
 * 개인정보처리방침 본문 — PrivacyPage 와 약관 동의 모달에서 공유.
 *
 * 정식 페이지 `/privacy` 와 /step 회원가입 동의 흐름의 "보기" 모달에서 동일 본문을
 * 노출하기 위해 본문만 추출. wrapping (page padding / max-width / shadow 등) 은
 * 호출처가 책임.
 */
export function PrivacyContent() {
  return (
    <div className="space-y-8 text-sm leading-7 text-gray-700 md:text-base">
      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제1조(목적)</h2>
        <p>
          withDOG 운영팀(이하 &quot;운영팀&quot;)은 이용자의 개인정보를 보호하고
          관련 법령을 준수하기 위하여 본 개인정보처리방침을 수립합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제2조(수집하는 개인정보 항목)</h2>
        <p className="mb-3">운영팀은 서비스 제공을 위해 다음 정보를 수집할 수 있습니다.</p>
        <ul className="list-disc space-y-2 pl-6">
          <li>회원 식별 정보: 이메일, 닉네임, 소셜 로그인 제공자, 소셜 로그인 식별 정보</li>
          <li>보호자 프로필 정보: 성별, 생년월일, 여행 성향 태그, 프로필 이미지</li>
          <li>반려견 정보: 이름, 견종, 생년월일, 성별, 중성화 여부, 성격 태그, 반려견 이미지</li>
          <li>서비스 이용 중 저장 정보: 채팅방, 채팅 메시지, 장소 추천 요청 및 응답, 즐겨찾기 장소</li>
          <li>다이어리 정보: 6하원칙 입력값, 제목, 본문, 요약, 감정, 일기 날짜, AI 생성 이미지</li>
          <li>이미지 정보: 업로드 파일명, 이미지 URL, 이미지 메타데이터</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제3조(개인정보 수집 방법)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>Google, Kakao, Naver 소셜 로그인 및 회원가입 과정</li>
          <li>보호자 및 반려견 프로필 등록·수정 과정</li>
          <li>이미지 업로드, 장소 추천, 챗봇, AI 그림일기 기능 이용 과정</li>
          <li>즐겨찾기, 캘린더, 마이페이지 등 저장 기능 이용 과정</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제4조(개인정보의 이용 목적)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>회원 식별, 로그인 유지, 계정 관리 및 회원 탈퇴 처리</li>
          <li>보호자와 반려견 프로필 기반 장소 추천 및 챗봇 응답 제공</li>
          <li>채팅 메시지 저장 및 대화 이력 제공</li>
          <li>AI 그림일기 생성, 이미지 생성·저장, 다이어리 이력 관리</li>
          <li>즐겨찾기, 캘린더, 마이페이지 등 개인화 기능 제공</li>
          <li>고객 문의 및 권리 행사 요청 처리</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제5조(개인정보의 보유 및 이용기간)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>회원 정보 및 프로필 정보: 회원 탈퇴 시까지</li>
          <li>반려견, 다이어리, 채팅, 즐겨찾기 정보: 회원 탈퇴 시까지 또는 이용자가 삭제할 때까지</li>
          <li>탈퇴 계정: 복구 및 재가입 정책 운영을 위해 탈퇴 후 10일간 별도 보관 후 삭제</li>
          <li>관련 법령에 따라 보존이 필요한 정보: 해당 법령에서 정한 기간</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제6조(개인정보의 제3자 제공)</h2>
        <p>
          운영팀은 원칙적으로 이용자의 개인정보를 외부에 제공하지 않습니다. 다만 이용자의
          동의가 있거나 법령에 특별한 규정이 있는 경우에는 예외로 합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제7조(개인정보 처리의 위탁 및 외부 서비스 이용)</h2>
        <p className="mb-3">
          운영팀은 원활한 서비스 제공을 위해 다음과 같이 개인정보 처리 업무의 일부를 위탁하거나
          외부 서비스를 이용할 수 있습니다.
        </p>
        <ul className="list-disc space-y-2 pl-6">
          <li>AWS: 서버 운영, 데이터베이스 운영, 이미지 저장 및 전송</li>
          <li>OpenAI: 챗봇 응답, AI 그림일기 본문 및 이미지 생성 등 AI 기능 제공</li>
          <li>Google, Kakao, Naver: 소셜 로그인 인증 및 사용자 식별</li>
          <li>지도·장소 정보 관련 외부 서비스: 장소 검색, 지도 표시, 위치 기반 정보 제공</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제8조(개인정보의 국외 이전)</h2>
        <p>
          운영팀은 AI 기능, 소셜 로그인, 클라우드 인프라 제공을 위해 일부 데이터가 국외 서버에서
          처리될 수 있는 외부 서비스를 이용할 수 있습니다. 이 경우 관련 법령이 요구하는 보호조치를
          이행합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제9조(위치 및 장소 정보 처리)</h2>
        <p>
          서비스는 반려견 동반 장소 추천과 지도 표시를 위해 장소의 주소, 위도, 경도, 운영 정보,
          동반 조건 등을 처리합니다. 이용자의 현재 위치를 사용하는 기능이 제공되는 경우에는
          이용자의 동의 또는 브라우저·기기 권한 설정에 따라 처리합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제10조(개인정보의 파기)</h2>
        <p className="mb-3">
          개인정보 보유기간의 경과, 처리 목적 달성 등 개인정보가 불필요하게 되었을 때에는
          지체 없이 해당 개인정보를 파기합니다.
        </p>
        <ul className="list-disc space-y-2 pl-6">
          <li>전자적 파일: 복구 불가능한 방식으로 삭제</li>
          <li>이미지 파일: 저장소 객체 삭제</li>
          <li>DB 저장 정보: 해당 레코드 삭제 또는 비식별 처리</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제11조(이용자의 권리와 행사 방법)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>이용자는 자신의 개인정보 조회, 수정, 삭제를 요청할 수 있습니다.</li>
          <li>개인정보 수집 및 이용 동의를 철회할 수 있습니다.</li>
          <li>회원탈퇴를 통해 개인정보 삭제를 요청할 수 있습니다.</li>
          <li>정정 또는 삭제 요청 시 운영팀은 지체 없이 필요한 조치를 합니다.</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제12조(아동의 개인정보보호)</h2>
        <p>
          운영팀은 만 14세 미만 아동의 개인정보 보호를 위해 만 14세 이상의 이용자에 한하여
          회원가입을 허용합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제13조(개인정보의 안전성 확보조치)</h2>
        <p>
          운영팀은 개인정보의 분실, 도난, 유출, 변조 또는 훼손을 방지하기 위해 접근권한 관리,
          암호화, 보안 점검 등 기술적·관리적 보호조치를 시행합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제14조(자동 수집 정보)</h2>
        <p>
          운영팀은 현재 접속 로그, 서비스 이용 기록, 쿠키 기반 추적 정보 등 자동 수집 정보를
          별도로 수집하지 않습니다. 다만 로그인 상태 유지를 위해 이용자의 브라우저 저장소에
          인증 토큰 등 최소한의 정보가 저장될 수 있습니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제15조(자동화된 결정에 대한 안내)</h2>
        <p>
          본 서비스는 AI와 자동화된 추천 로직을 활용하여 장소 추천, 챗봇 응답, 다이어리 본문 및
          이미지를 생성할 수 있습니다. 이용자는 자동화된 결과에 대해 설명을 요구하거나 문의할 수
          있습니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제16조(개인정보 보호책임자)</h2>
        <div className="rounded-xl bg-orange-50 p-4">
          <p>책임자: withDOG 운영팀</p>
          <p>문의: 서비스 내 문의 채널 또는 운영팀이 별도 공지한 연락처</p>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제17조(권익침해 구제방법)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>개인정보분쟁조정위원회: 1833-6972</li>
          <li>개인정보침해신고센터: 118</li>
          <li>대검찰청: 1301</li>
          <li>경찰청: 182</li>
        </ul>
      </section>

      <section className="border-t border-gray-200 pt-6">
        <h2 className="mb-3 text-lg font-semibold text-gray-900">부칙</h2>
        <p>본 방침은 2026년 5월 14일부터 시행됩니다.</p>
      </section>
    </div>
  );
}
