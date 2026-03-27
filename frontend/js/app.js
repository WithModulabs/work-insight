// Main Application Logic

// 네비게이션 및 섹션 전환
function navigateTo(sectionId) {
    // 모든 섹션 숨기기
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.classList.remove('active'));

    // 모든 네비게이션 아이템 비활성화
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));

    // 선택된 섹션 표시
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // 선택된 네비게이션 아이템 활성화
    const targetNav = document.querySelector(`[href="#${sectionId}"]`);
    if (targetNav) {
        targetNav.classList.add('active');
    }

    // 스크롤 상단으로
    window.scrollTo(0, 0);
}

// 기본 네비게이션 이벤트
document.addEventListener('DOMContentLoaded', () => {
    // 네비게이션 클릭 이벤트
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const href = item.getAttribute('href');
            if (href) {
                const sectionId = href.substring(1); // '#' 제거
                navigateTo(sectionId);
            }
        });
    });

    // 폼 제출 이벤트
    const reportForm = document.getElementById('report-form');
    if (reportForm) {
        reportForm.addEventListener('submit', (e) => {
            e.preventDefault();
            submitReport(reportForm);
        });
    }

    // 초기 섹션 표시
    navigateTo('home');
});

// 탭 여기기
function switchTab(tabId) {
    // 모든 탭 콘텐츠 숨기기
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));

    // 모든 탭 버튼 비활성화
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));

    // 선택된 탭 표시
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // 선택된 탭 버튼 활성화
    event.target.classList.add('active');
}

// 대시보드 뷰 전환
function switchDashboard(view) {
    const teamDashboard = document.getElementById('team-dashboard');
    const orgDashboard = document.getElementById('org-dashboard');

    if (view === 'team') {
        teamDashboard.style.display = 'block';
        orgDashboard.style.display = 'none';
    } else if (view === 'org') {
        teamDashboard.style.display = 'none';
        orgDashboard.style.display = 'block';
    } else if (view === 'custom') {
        teamDashboard.style.display = 'block';
        orgDashboard.style.display = 'block';
    }
}

// 시간 기반 인사말
function updateGreeting() {
    const hour = new Date().getHours();
    let greeting = '';

    if (hour < 12) {
        greeting = '좋은 아침입니다! 오늘 하루도 화이팅합시다 💪';
    } else if (hour < 18) {
        greeting = '오늘도 수고많으셨습니다. 남은 시간 화이팅 🔥';
    } else {
        greeting = '오늘 하루 정말 수고하셨습니다! 잠깐의 휴식을 즐기세요 😊';
    }

    const greetingElement = document.getElementById('greeting');
    if (greetingElement) {
        greetingElement.textContent = greeting;
    }
}

// 페이지 로드 시 인사말 업데이트
window.addEventListener('load', updateGreeting);

// 매 시간마다 인사말 업데이트
setInterval(updateGreeting, 3600000); // 1시간마다

// 실시간 통계 업데이트 (데모용)
function initializeRealtimeUpdates() {
    // 매분마다 통계 업데이트
    setInterval(() => {
        // 제출률 업데이트
        const today = new Date().getDate();
        const hour = new Date().getHours();
        const submission = Math.min(100, 70 + (hour * 3));

        // 주간 데이터 시뮬레이션
        if (Math.random() > 0.9) {
            const metricsValue = document.querySelector('.metric-value');
            if (metricsValue) {
                metricsValue.textContent = `${Math.max(70, submission)}%`;
            }
        }
    }, 60000); // 1분마다
}

// 페이지 로드 완료 후 실시간 업데이트 시작
window.addEventListener('load', initializeRealtimeUpdates);

// 키보드 단축키
document.addEventListener('keydown', (e) => {
    // Ctrl+K / Cmd+K로 Copilot 열기
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        navigateTo('copilot');
        setTimeout(() => {
            document.getElementById('copilot-query').focus();
        }, 100);
    }

    // Ctrl+R / Cmd+R로 보고 작성 창 열기
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        navigateTo('reports');
        setTimeout(() => {
            document.getElementById('accomplished').focus();
        }, 100);
    }
});

// 알람 권한 요청 (선택사항)
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// 시뮬레이션: 리스크 신호 업데이트
function simulateRiskSignalUpdates() {
    const riskAlerts = document.getElementById('risk-alerts');
    if (!riskAlerts) return;

    const signals = [
        {
            level: 'warning',
            message: '팀원 A: 최근 피로도 증가 추세',
            icon: '⚠️'
        },
        {
            level: 'high',
            message: '프로젝트 B: 2일 이상 지연 위험',
            icon: '🚨'
        },
        {
            level: 'attention',
            message: '팀원 C: 만족도 하락 신호',
            icon: '⚡'
        }
    ];

    riskAlerts.innerHTML = signals.map(signal => `
        <div style="
            padding: 10px;
            margin-bottom: 8px;
            background: var(--light-bg);
            border-left: 4px solid ${signal.level === 'high' ? '#E74C3C' : '#F39C12'};
            border-radius: 4px;
            font-size: 14px;
        ">
            <span>${signal.icon}</span> ${signal.message}
        </div>
    `).join('');
}

// 페이지 로드 시 리스크 신호 표시
window.addEventListener('load', () => {
    simulateRiskSignalUpdates();
    
    // 30초마다 업데이트
    setInterval(simulateRiskSignalUpdates, 30000);
});

// 대시보드 실시간 통계
function updateDailySummary() {
    const dailySummary = document.getElementById('daily-summary');
    if (!dailySummary) return;

    const today = new Date();
    const taskCount = Math.floor(Math.random() * 5) + 3;
    const completionRate = Math.floor(Math.random() * 40) + 60;

    dailySummary.innerHTML = `
        <div style="margin-bottom: 12px;">
            <div style="color: var(--light-text); font-size: 14px;">오늘의 핵심 업무</div>
            <div style="font-size: 20px; font-weight: bold; color: var(--primary-color); margin-top: 4px;">
                ${taskCount}개 항목
            </div>
        </div>
        <div>
            <div style="color: var(--light-text); font-size: 14px;">예상 완료율</div>
            <div style="font-size: 20px; font-weight: bold; color: var(--secondary-color); margin-top: 4px;">
                ${completionRate}%
            </div>
        </div>
    `;
}

// 페이지 로드 및 정기적 업데이트
window.addEventListener('load', updateDailySummary);
setInterval(updateDailySummary, 300000); // 5분마다

// 페이지 离開 시 경고
let hasUnsavedChanges = false;

document.addEventListener('change', () => {
    hasUnsavedChanges = true;
});

window.addEventListener('beforeunload', (e) => {
    if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
    }
});

// 폼 제출 후 저장 상태 초기화
document.addEventListener('submit', () => {
    hasUnsavedChanges = false;
});

// 헬퍼 함수: 날짜 포맷
function formatDate(date) {
    return new Date(date).toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// 헬퍼 함수: 상대 시간 표시
function getRelativeTime(date) {
    const now = new Date();
    const diff = now - new Date(date);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '방금';
    if (minutes < 60) return `${minutes}분 전`;
    if (hours < 24) return `${hours}시간 전`;
    if (days < 7) return `${days}일 전`;
    return formatDate(date);
}

// 애니메이션: 카운터 증가 효과
function animateCounter(element, startValue, endValue, duration = 1000) {
    let currentValue = startValue;
    const increment = (endValue - startValue) / (duration / 16);
    const timer = setInterval(() => {
        currentValue += increment;
        if (currentValue >= endValue) {
            currentValue = endValue;
            clearInterval(timer);
        }
        element.textContent = Math.floor(currentValue);
    }, 16);
}

// 에러 핸들링
window.addEventListener('error', (e) => {
    console.error('Application Error:', e);
    // 사용자 친화적인 에러 메시지 표시
    if (e.message.includes('API')) {
        showNotification('서버 연결에 문제가 있습니다. 나중에 다시 시도해주세요.', 'error');
    }
});

// 네트워크 상태 감지
window.addEventListener('online', () => {
    showNotification('연결이 복구되었습니다 🎉', 'success');
});

window.addEventListener('offline', () => {
    showNotification('인터넷 연결이 끊어졌습니다 ⚠️', 'error');
});

// 초기화 완료 메시지
console.log('%c✨ WorkInsight 애플리케이션 로드 완료!', 'color: #4A90E2; font-weight: bold; font-size: 14px;');
