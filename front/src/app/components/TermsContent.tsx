/**
 * 서비스 이용약관 본문 — TermsPage 와 약관 동의 모달에서 공유.
 *
 * 정식 페이지 `/terms` 와 /step 회원가입 동의 흐름의 "보기" 모달에서 동일 본문을
 * 노출하기 위해 본문만 추출. wrapping 은 호출처가 책임.
 */
export function TermsContent() {
  return (
    <div className="space-y-8 text-sm leading-7 text-gray-700 md:text-base">
      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제1조(목적)</h2>
        <p>
          이 약관은 withDOG 운영팀(이하 &quot;운영팀&quot;)이 제공하는 반려견 동반
          장소 추천 챗봇, 반려견 프로필 관리, AI 그림일기 생성·저장, 즐겨찾기,
          캘린더 등 관련 서비스의 이용과 관련하여 운영팀과 이용자 간의 권리·의무 및
          책임사항을 규정함을 목적으로 합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제2조(정의)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            &quot;서비스&quot;란 운영팀이 웹사이트 및 앱을 통해 제공하는 반려견 동반 장소 추천,
            챗봇 상담, 반려견·보호자 프로필 관리, AI 그림일기, 즐겨찾기, 캘린더 등 제반
            기능을 의미합니다.
          </li>
          <li>
            &quot;이용자&quot;란 본 약관에 따라 운영팀이 제공하는 서비스를 이용하는 회원 및
            비회원을 말합니다.
          </li>
          <li>
            &quot;회원&quot;이란 소셜 로그인 등을 통해 회원등록을 한 사람으로, 지속적으로
            서비스를 이용할 수 있는 자를 의미합니다.
          </li>
          <li>
            &quot;반려견 정보&quot;란 이용자가 등록한 반려견의 이름, 견종, 생년월일, 성별,
            성격 태그, 이미지 등 서비스 제공에 필요한 정보를 의미합니다.
          </li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제3조(약관의 게시와 개정)</h2>
        <p>
          운영팀은 본 약관의 내용을 이용자가 쉽게 알 수 있도록 서비스 초기 화면 또는 연결
          화면에 게시합니다. 운영팀은 관련 법령을 위반하지 않는 범위에서 본 약관을 개정할 수
          있으며, 개정 시 시행일과 개정 사유를 함께 공지합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제4조(회원가입 및 이용계약의 성립)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>이용계약은 이용자의 회원가입 신청과 운영팀의 승낙으로 성립합니다.</li>
          <li>이용자는 회원가입 및 프로필 등록 시 사실에 근거한 정보를 입력해야 합니다.</li>
          <li>허위 정보 또는 타인 정보를 이용한 가입 및 서비스 이용은 제한될 수 있습니다.</li>
          <li>운영팀은 기술상 또는 운영상 문제가 있는 경우 승낙을 유보하거나 거절할 수 있습니다.</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제5조(회원정보의 변경)</h2>
        <p>
          회원은 회원정보, 보호자 프로필, 반려견 정보에 변경이 있는 경우 지체 없이 이를
          수정해야 하며, 변경사항을 수정하지 않아 발생하는 불이익에 대한 책임은 회원 본인에게
          있습니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제6조(계정 및 인증정보 관리)</h2>
        <p>
          계정과 인증정보 관리 책임은 회원 본인에게 있습니다. 이를 제3자에게 양도, 대여하거나
          부정하게 사용해서는 안 되며, 관리 소홀로 인해 발생한 손해에 대한 책임은 회원에게
          있습니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제7조(서비스의 제공)</h2>
        <p className="mb-3">운영팀이 제공하는 서비스의 주요 내용은 다음과 같습니다.</p>
        <ul className="list-disc space-y-2 pl-6">
          <li>보호자 및 반려견 프로필 등록·수정·관리 서비스</li>
          <li>반려견 성향과 이용자 요청을 고려한 장소 추천 챗봇 서비스</li>
          <li>반려견 동반 장소 검색, 지도 표시, 상세 정보 및 즐겨찾기 서비스</li>
          <li>AI 기반 그림일기 본문·요약·이미지 생성 및 저장 서비스</li>
          <li>다이어리 앨범, 캘린더, 즐겨찾기 등 기록 관리 서비스</li>
          <li>서비스 개선을 위한 통계, 오류 대응, 품질 관리 기능</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제8조(서비스 이용시간 및 변경)</h2>
        <p>
          서비스는 특별한 사정이 없는 한 연중무휴, 1일 24시간 제공을 원칙으로 합니다. 다만
          시스템 점검, 유지보수, 장애 대응, 외부 연동 서비스 이슈 등으로 인해 서비스의 전부
          또는 일부가 일시 중단될 수 있습니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제9조(AI 및 추천 서비스의 한계)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            장소 추천, 챗봇 응답, AI 그림일기 결과는 자동화된 모델과 추천 로직을 통해 생성되는
            참고용 정보입니다.
          </li>
          <li>
            추천 결과는 입력 정보, 장소 데이터, 외부 API 상태, 모델 응답에 따라 달라질 수 있으며
            정확성·완전성·최신성을 보장하지 않습니다.
          </li>
          <li>
            장소의 영업시간, 반려견 동반 가능 여부, 입장 조건, 요금, 안전 정보는 실제 현장
            사정에 따라 달라질 수 있으므로 방문 전 공식 채널을 통해 확인해야 합니다.
          </li>
          <li>
            챗봇 응답은 수의학적 진단, 의료행위, 법률·전문 상담을 대체하지 않습니다. 반려견의
            건강 이상이 의심되는 경우 수의사 등 전문가와 상담해야 합니다.
          </li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제10조(이미지 및 콘텐츠 업로드 관련 특칙)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>이용자는 본인에게 권리가 있거나 적법한 권한을 가진 이미지와 콘텐츠만 업로드해야 합니다.</li>
          <li>타인의 저작권, 초상권, 개인정보, 명예를 침해할 수 있는 이미지 또는 콘텐츠를 업로드해서는 안 됩니다.</li>
          <li>운영팀은 서비스 제공을 위해 업로드된 이미지와 입력 내용을 저장, 분석, 처리할 수 있습니다.</li>
          <li>운영팀은 관련 법령 또는 약관 위반 콘텐츠를 사전 통지 없이 삭제하거나 이용 제한 조치를 할 수 있습니다.</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제11조(이용자의 의무)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>허위 정보 입력, 타인 정보 도용, 부정 사용을 해서는 안 됩니다.</li>
          <li>관련 법령, 본 약관, 운영정책, 공지사항을 준수해야 합니다.</li>
          <li>서비스를 비정상적으로 이용하거나 운영을 방해하는 행위를 해서는 안 됩니다.</li>
          <li>자동화된 요청, 스팸, 악성 코드 전송, 서비스 취약점 탐색 등 부정 이용을 해서는 안 됩니다.</li>
          <li>계정 보안 및 회원정보 최신성 유지 의무는 이용자에게 있습니다.</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제12조(서비스 이용의 제한)</h2>
        <p>
          운영팀은 이용자가 본 약관 또는 관련 법령을 위반하는 경우, 사안의 경중에 따라 서비스
          이용 제한, 콘텐츠 삭제, 계정 이용 정지 또는 계약 해지 조치를 취할 수 있습니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제13조(개인정보보호)</h2>
        <p>
          운영팀은 관련 법령이 정하는 바에 따라 이용자의 개인정보를 보호하기 위해 노력하며,
          개인정보의 수집·이용·보관·파기 등에 관한 사항은 별도의 개인정보처리방침에 따릅니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제14조(자동화된 결정에 대한 안내)</h2>
        <p>
          본 서비스의 일부 결과는 자동화된 시스템에 의해 생성될 수 있습니다. 이용자는 이러한
          자동화된 결과에 대해 설명을 요구하거나 문의할 수 있습니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제15조(면책사항)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>천재지변 또는 이에 준하는 불가항력으로 인한 서비스 장애</li>
          <li>이용자의 귀책사유로 인한 서비스 이용 장애</li>
          <li>외부 로그인, 지도, 클라우드, AI API 등 제3자 서비스 장애로 인한 서비스 제한</li>
          <li>이용자가 서비스에서 제공된 추천 정보 또는 AI 생성 결과를 활용해 발생한 손해</li>
          <li>실제 장소 정보와 서비스 내 표시 정보의 차이로 인해 발생한 손해</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제16조(권리의 귀속)</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>운영팀이 제공하는 서비스 및 관련 저작물에 대한 지식재산권은 운영팀에 귀속됩니다.</li>
          <li>이용자가 직접 작성하거나 업로드한 콘텐츠 및 이미지의 권리는 해당 이용자에게 귀속됩니다.</li>
          <li>운영팀은 서비스 제공, 저장, 백업, 표시, 품질 개선을 위해 이용자 콘텐츠를 필요한 범위에서 이용할 수 있습니다.</li>
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제17조(계약 해지 및 탈퇴)</h2>
        <p>
          이용자는 언제든지 서비스 내 회원탈퇴 기능을 통해 이용계약 해지를 요청할 수 있습니다.
          운영팀은 관련 법령 및 개인정보처리방침에 따라 필요한 정보를 보관한 뒤 파기합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">제18조(준거법 및 관할법원)</h2>
        <p>
          본 약관은 대한민국 법령에 따라 해석되며, 서비스와 관련하여 분쟁이 발생하는 경우
          민사소송법상 관할법원을 전속적 합의관할로 합니다.
        </p>
      </section>

      <section className="border-t border-gray-200 pt-6">
        <h2 className="mb-3 text-lg font-semibold text-gray-900">부칙</h2>
        <p>본 약관은 2026년 5월 14일부터 시행됩니다.</p>
      </section>
    </div>
  );
}
