# AI SPEC — Hỗ trợ tự đánh giá sau Giai đoạn 1 · Nhóm B21 · Zone 3
Hướng: [x] B — Vlearn
Loại: [x] Tính năng mới

## §1. User & Job
- Job executor + workflow: học viên khóa đào tạo chuyên sâu sau khi hoàn thành Giai đoạn 1 đang cần tự đánh giá chính xác thế mạnh chuyên môn, mức độ hoàn thành Lab và Quiz tích lũy trước khi chọn nhánh định hướng ở Giai đoạn 2.
- Core JTBD: giúp học viên nhanh chóng hiểu điểm mạnh, điểm yếu và nhánh phù hợp nhất để giảm rủi ro chọn sai.
- Problem statement: học viên đang mất thời gian tự suy đoán, hay bối rối khi không biết mình phù hợp nhánh nào, dẫn đến chọn sai và phải làm lại dự án.
- Evidence (chuẩn A/B):
  - Mining: từ dữ liệu mock và giả định luồng học viên, có các dấu hiệu chung về mất định hướng sau Giai đoạn 1, gồm: khó tự đánh giá điểm mạnh, chưa rõ Lab/Quiz tích lũy, lo lắng khi chọn nhánh.
  - Ví dụ nguyên văn: "Em không biết mình phù hợp nhánh nào", "Em thấy Lab làm được nhưng không biết có đủ tốt không", "Quiz có điểm cao nhưng em vẫn không chắc mình nên đi đâu".

## §2. Impact & quyết định chọn
- Bảng impact:
  | Ứng viên | Số người gặp | Tần suất | Mỗi lần tốn gì | Khả thi build | Chọn |
  |---|---:|---:|---|---|---|
  | Học viên chưa rõ nhánh | 30 | thường xuyên | 30-60 phút suy nghĩ + có thể làm lại dự án | Cao | Có |
  | Trợ giảng tư vấn 1:1 | 15 | thường xuyên | 20-30 phút mỗi học viên | Cao | Có |
  | Giảng viên theo dõi tiến độ | 10 | định kỳ | mất thời gian tổng hợp | Trung bình | Có |
- Ứng viên đã loại: học viên không cần định hướng ngay vì đã có mục tiêu rõ ràng.
- Ứng viên chọn: học viên sau Giai đoạn 1 cần một công cụ hỗ trợ tự đánh giá nhanh và gợi ý nhánh phù hợp.

## §3. Giải pháp tương tự đã nghiên cứu
- ChatGPT study mode: hữu ích cho tư vấn chung nhưng thiếu bối cảnh học tập cụ thể và không theo đúng cấu trúc nhánh của khoá.
- Quizlet AI: phù hợp quiz nhưng không gắn với quá trình học và định hướng nghề nghiệp.
- NotebookLM: mạnh ở truy xuất tài liệu nhưng không phù hợp cho quyết định nhánh học tập ngắn gọn.
- Điểm khác biệt: prototype này tập trung vào 3 vấn đề cốt lõi của Giai đoạn 1 — tự đánh giá, Lab, Quiz — và gắn trực tiếp với lựa chọn nhánh ở Giai đoạn 2.

## §4. Thiết kế
- Lát cắt một câu: một học viên sau Giai đoạn 1 cần tự đánh giá Lab/Quiz và nhận gợi ý nhánh phù hợp để chọn đúng hướng học tiếp.
- Non-goals: không tự động ghi danh, không thay đổi hồ sơ học viên, không dùng dữ liệu thật của người thật, không thay thế tư vấn 1:1 hoàn toàn.
- Mức prototype nhắm tới: [x] Working — phần đánh giá và gợi ý chạy được, phần chat có thể dùng mock fallback.
- Automation: [x] conditional — hệ thống tự đánh giá khi có đủ dữ liệu và hỏi lại khi câu hỏi ngoài phạm vi; nếu thiếu căn cứ thì chuyển sang giới hạn phạm vi.
- §4b. Nguyên tắc đã áp dụng:

| Nguyên tắc | Áp cụ thể vào đâu trong prototype |
|---|---|
| G1 — Làm rõ phạm vi hệ thống | UI và chatbot đều nhấn mạnh đây là công cụ hỗ trợ tự đánh giá sau Giai đoạn 1, không thay thế quyết định của học viên hoặc giảng viên |
| G2 — Làm rõ độ tin cậy | Mỗi gợi ý nhánh được xây dựng từ dữ liệu điểm Lab, Quiz tích lũy và điểm mạnh chuyên môn để học viên thấy rõ căn cứ |
| G10 — Thu hẹp phạm vi khi nghi ngờ | Khi học viên hỏi ngoài phạm vi như thời tiết, đời sống cá nhân hoặc câu hỏi không liên quan định hướng nhánh, chatbot trả về phản hồi out_of_scope |
| G11 — Giải thích vì sao | Mỗi nhánh đề xuất đều đi kèm lý do bằng dữ liệu và chỉ số cụ thể, giúp học viên hiểu vì sao mình phù hợp với nhánh đó |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản
- ① Nguồn sự thật: AI bịa ra điểm mạnh hoặc gợi ý không dựa trên dữ liệu đầu vào.
- ② Mơ hồ / thiếu thông tin: học viên chưa cung cấp đầy đủ điểm số hoặc câu hỏi mơ hồ.
- ③ Ngoài phạm vi: hỏi về chuyện cá nhân hoặc đời sống ngoài nhánh định hướng.
- ④ Đặc thù domain: nhánh đúng không đơn thuần là điểm số, cần bảo vệ tính phù hợp với bối cảnh khoá học.

Kịch bản:
1. Học viên nhập thiếu điểm Lab/Quiz ⇒ hệ thống báo dữ liệu chưa đủ.
2. AI đưa ra nhánh không liên quan tới điểm mạnh ⇒ hệ thống cần giải thích bằng dữ liệu.
3. Học viên hỏi ngoài phạm vi ⇒ chatbot trả về out_of_scope.
4. Một học viên có điểm kỹ thuật cao nhưng yếu product ⇒ hệ thống ưu tiên nhánh phù hợp hơn.
5. Một học viên có điểm Lab thấp nhưng Quiz tốt ⇒ hệ thống hiển thị cả hai chỉ số.
6. Học viên muốn biết “nên chọn nhánh nào” ⇒ hệ thống trả gợi ý dựa trên snapshot.
7. Học viên hỏi “thời tiết hôm nay” ⇒ chatbot từ chối và thu hẹp phạm vi.
8. Học viên có điểm mạnh ở infrastructure nhưng chưa đủ Lab ⇒ hệ thống vẫn đưa ra căn cứ rõ ràng.

## §6. Bốn đường đi của trải nghiệm
- Happy path: học viên xem hồ sơ, tạo assessment, thấy kết quả tự đánh giá và nhánh phù hợp nhất.
- Low-confidence: học viên thấy chỉ số Lab/Quiz không đủ chắc, hệ thống đề xuất học thêm hoặc kiểm tra lại.
- Failure/không căn cứ: hệ thống không tự động kết luận mà nêu rõ dữ liệu dùng để đánh giá.
- Correction: học viên có thể tiếp tục hỏi chatbot để làm rõ vì sao nhánh đó phù hợp.
- Khi bị đòi ngoài phạm vi: chatbot trả về out_of_scope.
- Case đặc thù domain: hệ thống giữ nguyên mục tiêu định hướng học tập trong khoá, không vượt phạm vi.

## §7. Kiểm thử
- Chiều chất lượng: đúng dữ liệu, giải thích được căn cứ, phạm vi rõ ràng.
- Golden set: 24 case gồm 8 case khó, 12 case thường, 4 case hiếm.
- Quality bar: đạt khi ≥75% case trả về kết quả đúng schema và ≥70% case có giải thích căn cứ rõ ràng.
- Kết quả các lượt chạy: bảng được lưu trong eval/.

## §8. Phân công & kế hoạch

| Vai trò | Người phụ trách | Nhiệm vụ chính |
|---|---|---|
| Spec & Evidence | Người 1 | Viết spec, định nghĩa user/job, impact, lát cắt và các kịch bản lỗi; chuẩn bị bằng chứng đầu vào cho phần §1-§2. |
| Data & Prompt | Người 2 | Chuẩn bị mock data, kiểm tra schema dữ liệu đầu vào, xây dựng prompt cho hệ thống AI và tối ưu cách chatbot trả lời theo phạm vi đề tài. |
| Backend & Logic | Người 3 | Phát triển backend/API, logic tạo assessment, tính Lab completion/Quiz score và kết nối với provider AI. |
| Frontend & UX | Người 4 | Phát triển giao diện web, hiển thị tự đánh giá, kết quả nhánh và trải nghiệm chat cho học viên. |
| Evaluation & Demo | Người 5 | Chuẩn bị golden set, bảng kết quả chạy, validation feedback và slide demo cho vòng trình bày. |

| Giai đoạn | Mục tiêu |
|---|---|
| Giai đoạn 1 | Thống nhất spec, evidence và flow chính. |
| Giai đoạn 2 | Xây dựng prototype chạy được và có ít nhất 1 lời gọi AI thật. |
| Giai đoạn 3 | Chạy golden set, ghi feedback và chuẩn bị demo. |

- Willing users: 3 người ngoài nhóm sẽ thử nghiệm ở vòng validation.
- Multi-prototype: không áp dụng.

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| CP2 | Hoàn thiện flow UI và API | Đảm bảo prototype có thể bấm được |
| CP3 | Thêm mock fallback provider | Đảm bảo AI thật/giả đều chạy được |
| CP5 | Cập nhật UI hiển thị tự đánh giá | Phù hợp với mục tiêu đề tài |
