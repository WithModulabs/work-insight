// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8002/api';

// Mock API responses (프로토타입용)
const mockApiResponses = {
    '/reports/': {
        method: 'POST',
        handle: (data) => ({
            id: Math.floor(Math.random() * 1000),
            ...data,
            created_at: new Date().toISOString(),
            sentiment_score: Math.random() * 2 - 1,
            risk_level: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)],
            fatigue_level: Math.random(),
        })
    },
    '/reports/my/': {
        method: 'GET',
        handle: () => [{
            id: 1,
            author_id: 1,
            report_date: new Date().toISOString(),
            accomplished: '프로젝트 A 진행 회의 참석 및 스펙 정의',
            not_completed: '데이터베이스 구조 설계',
            tomorrow_plan: '스키마 작성 및 모델 구현',
            sentiment_score: 0.25,
            risk_level: 'medium',
            fatigue_level: 0.6,
            created_at: new Date().toISOString(),
        }]
    },
    '/copilot/query': {
        method: 'POST',
        handle: (query) => ({
            response_text: `"${query.query_text}"에 대한 종합 분석: 최근 7일간의 데이터를 기반으로 분석한 결과, 프로젝트 진행 상황은 양호하나 팀 리소스 배치 재검토가 필요합니다.`,
            evidence: [
                {
                    source: 'daily_report',
                    content: '관련 퇴근보고 데이터 참고',
                    date: new Date().toISOString(),
                },
                {
                    source: 'oneone',
                    content: '1:1 상담 기록 분석',
                    date: new Date().toISOString(),
                }
            ],
            confidence_score: 0.82,
            suggested_follow_ups: [
                '이 결론의 근거가 무엇인가요?',
                '어떤 리소스 재배치를 권고하나요?',
                '우선순위는?'
            ]
        })
    },
    '/copilot/suggestions': {
        method: 'GET',
        handle: () => [
            { question: '이번 주 가장 위험한 프로젝트는?', category: 'status' },
            { question: '우리 팀에서 케어가 필요한 사람은?', category: 'people' },
            { question: '최근 반복되는 이슈는?', category: 'analysis' },
        ]
    },
};

// API 호출 함수
async function apiCall(endpoint, method = 'GET', data = null) {
    // 프로토타입용 모의 API
    const mockResponse = mockApiResponses[endpoint];
    if (mockResponse && mockResponse.method === method) {
        return {
            status: 200,
            data: mockResponse.handle(data)
        };
    }

    // 실제 구현에서는 아래 코드 사용:
    /*
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();

        return {
            status: response.status,
            data: result
        };
    } catch (error) {
        console.error('API Error:', error);
        return {
            status: 500,
            error: error.message
        };
    }
    */
}

// 퇴근보고 제출
async function submitReport(form) {
    const formData = new FormData(form);
    const reportData = {
        accomplished: document.getElementById('accomplished').value,
        not_completed: document.getElementById('not-completed').value || null,
        tomorrow_plan: document.getElementById('tomorrow-plan').value || null,
        issues: document.getElementById('issues').value || null,
        support_needed: document.getElementById('support').value || null,
        collaboration_needed: document.getElementById('collaboration').value || null,
        fatigue_level: parseFloat(document.getElementById('fatigue').value) / 5,
    };

    const response = await apiCall('/reports/', 'POST', reportData);
    
    if (response.status === 200) {
        showNotification('보고가 제출되었습니다!', 'success');
        form.reset();
    } else {
        showNotification('제출에 실패했습니다.', 'error');
    }
}

// Copilot 쿼리 제출
async function submitCopilotQuery(event) {
    event.preventDefault();
    
    const query = document.getElementById('copilot-query').value;
    if (!query.trim()) return;

    // 로딩 상태
    const responseDiv = document.getElementById('copilot-response');
    responseDiv.style.display = 'block';
    document.getElementById('response-content').innerHTML = '분석 중입니다... ⏳';

    const response = await apiCall('/copilot/query', 'POST', { query_text: query });
    
    if (response.status === 200) {
        const data = response.data;
        document.getElementById('response-content').innerHTML = `
            <strong>📝 응답:</strong><br>
            ${escapeHtml(data.response_text)}<br><br>
            <strong>신뢰도:</strong> ${(data.confidence_score * 100).toFixed(0)}%
        `;
        
        document.getElementById('response-evidence').innerHTML = `
            <strong>📚 근거:</strong><br>
            ${data.evidence.map(e => `
                <div style="margin: 8px 0; padding: 8px; background: #f5f5f5; border-radius: 4px;">
                    <small><strong>${e.source}:</strong> ${escapeHtml(e.content)}</small>
                </div>
            `).join('')}
            <br>
            <strong>💡 추천 질문:</strong><br>
            ${data.suggested_follow_ups.map(q => 
                `<button class="question-btn" onclick="askCopilot('${escapeHtml(q)}')">${escapeHtml(q)}</button>`
            ).join('')}
        `;
    } else {
        document.getElementById('response-content').innerHTML = '오류가 발생했습니다.';
    }
}

// 추천 Copilot 질문
function askCopilot(question) {
    document.getElementById('copilot-query').value = question;
    document.getElementById('copilot-form').dispatchEvent(new Event('submit'));
}

// 유틸리티 함수
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#50C878' : '#E74C3C'};
        color: white;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 초기화 후 API로부터 데이터 로드
async function loadInitialData() {
    // 추천 질문 로드
    const suggestionsResponse = await apiCall('/copilot/suggestions', 'GET');
    if (suggestionsResponse.status === 200) {
        const suggestionsDiv = document.getElementById('suggested-questions');
        suggestionsDiv.innerHTML = suggestionsResponse.data.map(q =>
            `<button class="question-btn" onclick="askCopilot('${escapeHtml(q.question)}')">
                ${escapeHtml(q.question)}
            </button>`
        ).join('');
    }

    // 내 보고 로드
    const reportsResponse = await apiCall('/reports/my/', 'GET');
    if (reportsResponse.status === 200) {
        const reportsList = document.getElementById('my-reports');
        reportsList.innerHTML = reportsResponse.data.map(r => `
            <div class="report-card" style="padding: 12px; background: var(--light-bg); border-radius: 6px; margin-bottom: 10px;">
                <div><strong>📅 ${new Date(r.report_date).toLocaleDateString('ko-KR')}</strong></div>
                <div style="margin-top: 8px; font-size: 14px;">
                    <div><strong>완료:</strong> ${escapeHtml(r.accomplished.substring(0, 50))}...</div>
                    <div style="color: var(--light-text); margin-top: 4px;">
                        리스크: <strong>${r.risk_level}</strong> | 
                        감정: <strong>${(r.sentiment_score * 100).toFixed(0)}%</strong>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

// 피로도 슬라이더 라벨 업데이트
document.addEventListener('DOMContentLoaded', () => {
    const fatigueSlider = document.getElementById('fatigue');
    if (fatigueSlider) {
        fatigueSlider.addEventListener('input', (e) => {
            const labels = ['완전함', '신선함', '보통', '피곤', '매우 피곤', '업무 불가'];
            document.getElementById('fatigue-label').textContent = labels[parseInt(e.target.value)];
        });
    }

    // 초기 데이터 로드
    loadInitialData();
});
