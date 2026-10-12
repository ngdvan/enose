# Nhận xét luận án và bản tóm tắt đối chiếu V3

Ngày rà soát: 12/10/2026.

Báo cáo có **110 mục nhận xét**: 28 mục dữ liệu/giao thức, 23 mục diễn đạt chuyên môn/kết luận, 19 mục tham chiếu/trình bày và 40 mục chính tả/viết thiếu. Đây là số mục nhận xét, không phải 110 lỗi khoa học đã được chứng minh; một số mục là yêu cầu xác minh hoặc thống nhất biên tập, được ghi rõ bên dưới.

Hai tệp được rà soát: **6.Luan van tien si_T102026_V1.docx** (ký hiệu **LA**) và **7.Tom tat luan an TS_T102026_V1.docx** (ký hiệu **TT**). Nguồn đối chiếu chính là `Sensor_Aware_Transfer_Learning/V3.0`, đặc biệt bản Clean, Supplementary Evidence và xác nhận thu thập dữ liệu của tác giả. V3 được dùng để kiểm tra phần học chuyển giao và những mô tả dữ liệu dùng chung; không coi V3 là nguồn chứng minh mọi kết quả ở Chương 1–3.

Các nhận xét dưới đây có trích đoạn để tìm bằng Ctrl+F trong Word, vị trí mục/bảng và mã đoạn **P**. P là thứ tự nút đoạn trong `word/document.xml`, tính từ 1, bao gồm đoạn trống, ô bảng và các nhánh hình/textbox; **không phải số trang**. Khi có nhiều vị trí của cùng lỗi, chúng được gộp thành một nhận xét. Không đếm phần XML dự phòng của hình/textbox thành nội dung lặp trên trang.

**Mức ưu tiên:** **Cao** = ảnh hưởng số liệu, giao thức, kết luận hoặc khả năng tái lập; **Vừa** = diễn đạt chuyên môn, thiếu giải thích hoặc tham chiếu sai; **Nhẹ** = chính tả, tên gọi và trình bày. **Cần xác minh** nghĩa là chưa đủ căn cứ để thay bằng một thông tin mới.

Rà soát đã bao gồm văn bản, bảng, công thức OMML, tham chiếu và kiểm tra trực quan các hình 4.1–4.3 trích từ LA. Chưa render toàn bộ DOCX thành trang; do đó chưa xác nhận các lỗi ngắt trang, tràn lề, chồng hình hoặc font trên từng trang. Các nhận xét trình bày dưới đây chỉ nêu lỗi có bằng chứng trong nội dung/cấu trúc hoặc hình đã xem. Không sửa nội dung hai tệp gốc và không chạy lại các thí nghiệm.

## Các điểm cần sửa trước

1. NH₃/H₂: sửa **5 ngày** thành **6 ngày** theo xác nhận V3; bỏ khẳng định đã đo/kiểm soát **25 °C, RH 82%** nếu không có hồ sơ mới.
2. CO/ethylene: đánh giá chính cuốn chiếu dùng **7 khối**, không phải 5 khối; 5 khối thuộc phép chia cố định thứ yếu.
3. Sửa các siêu tham số bị chép sai: tốc độ học Scratch **5 × 10⁻⁴** và weight decay của supervised drift **2 × 10⁻⁴**.
4. Sửa nhận định Fine-tuned tốt nhất ở H₂: SVR có MAE trung bình **31,37**, thấp hơn **31,60 ppm**.
5. Bổ sung giới hạn thống kê V3: khoảng NH₃ sau hiệu chỉnh bốn so sánh là **[−0,60; 9,46] ppm**, chứa 0.
6. Kiểm tra lại Bảng 3.5: **MAE 39,87 > RMSE 35,72** cho NH₃/AE–LSTM–16 không thể đúng nếu cùng mẫu và cùng cách tổng hợp.
7. Làm rõ cách fit chuẩn hóa và cách tổ chức chuỗi AE–LSTM; hai vấn đề này ảnh hưởng tính hợp lệ của đánh giá Chương 3.

## A Nhất quán dữ liệu và giao thức

### A01 Cao — Số ngày đo NH₃/H₂ mâu thuẫn V3

**Vị trí:** LA §2.4.2, P1915; TT §2.4, P308. **Trích:** “trong 5 ngày đo khác nhau”; “6 lần đo trong 5 ngày”.

**Nhận xét:** Xác nhận tác giả trong V3 ghi quá trình thu thập diễn ra trong **sáu ngày**. Sáu lần lặp của thiết kế không đồng nghĩa với sáu phân vùng đánh giá là sáu ngày đo độc lập. **Đề xuất:** ghi “Thu thập dữ liệu diễn ra trong sáu ngày; dữ liệu gồm 378 lần phơi khí”. Giải thích riêng số lần lặp, số định danh và số phân vùng; chỉ nối lần đo với ngày khi có log. **Nguồn:** V3 `evidence/author_confirmations.md`, Clean §IV.A.

### A02 Cao — Nhiệt độ và độ ẩm NH₃/H₂ được khẳng định trái V3

**Vị trí:** LA §2.4.2, P1915; TT P308. **Trích:** “nhiệt độ 25 °C và độ ẩm tương đối (RH) 82%”; “Việc kiểm soát các thông số môi trường này”.

**Nhận xét:** V3 xác nhận nhiệt độ và độ ẩm **không được kiểm soát, không được đo/ghi nhận**. Không được giữ các con số này như điều kiện thực nghiệm đã xác minh. **Đề xuất:** “Nhiệt độ và độ ẩm không được kiểm soát hoặc đo ghi trong quá trình thu thập, nên chưa định lượng được ảnh hưởng của môi trường.” Nếu có hồ sơ mới, dẫn hồ sơ và giải thích vì sao khác V3. **Nguồn:** V3 author confirmations; Clean §IV.D, §VI.

### A03 Vừa — Khẳng định môi trường “độ ẩm cao” thiếu phép đo

**Vị trí:** LA P1395, P1494, P1922, P2148; TT P300. **Trích:** “môi trường đo thực tế với độ ẩm cao”.

**Nhận xét:** Với NH₃/H₂, V3 không có số đo độ ẩm. Vì vậy không thể dùng độ ẩm cao đã định lượng hoặc sự biến thiên môi trường đã chứng minh làm ưu thế dữ liệu. **Đề xuất:** mô tả thiết lập đo thực tế và giới hạn thiếu số đo; phân biệt bối cảnh dự kiến với điều kiện đã ghi nhận. Với VOCs, yêu cầu nguồn riêng, không suy từ NH₃/H₂.

### A04 Cao — Chép sai số khối CO/ethylene trong đánh giá chính

**Vị trí:** LA §4.4.2, P3832. **Trích:** “chia thành năm khối và sử dụng để đánh giá ba lần đánh giá cuốn chiếu”.

**Nhận xét:** V3 dùng **bảy khối** cho ba fold cuốn chiếu, mỗi fold gồm 3 khối pretrain + 1 adaptation + 1 future test. Năm khối chỉ đủ mô tả một cửa sổ phân vai như trên. **Đề xuất:** đổi thành bảy khối ở giao thức chính; giữ năm khối × 49 lần phơi khí ở P3833 cho phép chia cố định thứ yếu. **Nguồn:** Clean §IV.B.

### A05 Cao — Chép sai tốc độ học Scratch ở hai giao thức

**Vị trí:** LA §4.4.4, P3855, P3857. **Trích:** “15×10-4”.

**Nhận xét:** Cả Scratch trên đáp ứng thô và encoder Scratch trên drift dùng **5 × 10⁻⁴** trong V3, không phải 15 × 10⁻⁴. **Đề xuất:** sửa cả hai vị trí; đồng bộ mọi bảng cấu hình. **Nguồn:** Clean §IV.D; V3 `code/same_device_session_transfer.py` phần `fit_policy`, `code/revision_drift.py` phần nhóm optimizer.

### A06 Cao — Chép sai weight decay của supervised drift

**Vị trí:** LA §4.4.4, P3857. **Trích:** “hệ số suy giảm trọng số 10-4”.

**Nhận xét:** V3 báo cáo và triển khai **2 × 10⁻⁴** ở supervised drift. **Đề xuất:** sửa thành 2 × 10⁻⁴; không nhầm với weight decay **10⁻⁴ của pretraining**. **Nguồn:** Clean §IV.D; V3 `code/revision_drift.py`.

### A07 Vừa — Gọi khoảng phân vị 10–90 là “khoảng tứ phân vị”

**Vị trí:** LA P3856. **Trích:** “khoảng tứ phân vị thứ 10 đến phân vị thứ 90”.

**Nhận xét:** IQR là Q₇₅ − Q₂₅. Thang chuẩn hóa drift trong V3 là Q₉₀ − Q₁₀. **Đề xuất:** “chuẩn hóa robust với trung vị và khoảng chênh lệch giữa phân vị 90 và phân vị 10”. Giữ IQR cho giao thức đáp ứng thô nếu dùng Q₇₅ − Q₂₅.

### A08 Cao — Thiếu giới hạn độc lập ngày đo trong Chương 4

**Vị trí:** LA §4.4.1, P3825–P3826; §4.6, P4577–P4579; TT §4.3.2, P652. **Trích:** “dựa trên các hỗn hợp khí đo liên tiếp”; “kiểm định mở rộng trên nhiều phiên”.

**Nhận xét:** V3 chia theo các định danh Combination liên tiếp, không theo ngày. Thiếu log liên kết lần phơi khí với ngày nên các vai trò train/test có thể dùng chung ngày thu thập. **Đề xuất:** bổ sung rõ “held-out identifier partitions, chưa chứng minh tổng quát hóa giữa các ngày”; tránh dùng “phiên” theo nghĩa acquisition session độc lập. **Nguồn:** Clean §IV.A, §VI; Supplementary phần Acquisition independence; `evidence/SOURCE_NOTES.md` cảnh báo biến `sessions` kế thừa chỉ phân vùng định danh.

### A09 Cao — Khoảng tin cậy chưa hiệu chỉnh bị diễn giải quá mạnh

**Vị trí:** LA P3924, P3951, P4577; TT P652; tiêu đề Bảng 4.2 ở cả hai bản. **Trích:** “giảm sai số MAE đáng kể trên cả 4 khí”; “các khoảng tin cậy 95% ... đều nằm phía dương”.

**Nhận xét:** Các khoảng 95% trong bảng là **chưa hiệu chỉnh nhiều so sánh**. V3 bổ sung Bonferroni cho bốn so sánh: khoảng NH₃ 98,75% là [−0,60; 9,46] ppm, chứa 0. **Đề xuất:** ghi rõ “95% chưa hiệu chỉnh” trong tiêu đề; bổ sung kết quả độ nhạy và nhận định NH₃ là trường hợp yếu nhất. Giữ kết luận có điều kiện trên dữ liệu đã quan sát; CO/ethylene chỉ có ba fold. **Nguồn:** Clean §IV.E, §V.B; Supplementary Table S9.

### A10 Cao — Kết luận tốt nhất ở H₂ sai ngay theo bảng

**Vị trí:** LA P4321, Bảng 4.6; TT P825 và bảng ngay trước đoạn. **Trích:** “đạt hiệu năng tốt nhất trên khí H2”; “đạt MAE thấp nhất đối với H2”.

**Nhận xét:** Bảng cho SVR = **31,37 ± 4,53**, Fine-tuned = **31,60 ± 2,29 ppm**. Fine-tuned không có MAE trung bình thấp nhất. Ở ethylene, **Extra Trees 1,398 < Generic SSL 1,437 < Fine-tuned 1,627**; vì vậy câu LA “Generic SSL đạt sai số thấp nhất ... ở Ethylene” cũng sai. **Đề xuất:** báo cáo thứ hạng trung bình đúng: Generic SSL tốt nhất NH₃, SVR tốt nhất H₂, PLSR tốt nhất CO, Extra Trees tốt nhất ethylene; không biến thứ hạng trung bình thành ưu thế thống kê. **Nguồn:** bảng của hai bản; Clean §V.E và Table IV.

### A11 Cao — MAE lớn hơn RMSE trong Bảng 3.5

**Vị trí:** LA Bảng 3.5, P3102 và hàng AE–LSTM–16. **Trích số liệu:** NH₃: RMSE **35.72**, MAE **39.87**.

**Nhận xét:** Với cùng tập phần dư, MAE ≤ RMSE. Nếu cùng fold và cùng trọng số, lấy trung bình qua fold vẫn giữ bất đẳng thức. Sai khác 4,15 ppm không thể do làm tròn. **Đề xuất:** kiểm tra xuất số liệu, thứ tự cột, mô hình và tập đánh giá; không tự thay một trong hai số khi chưa có dữ liệu gốc. Nếu dùng cách tổng hợp khác nhau, mô tả và báo cáo lại trên cùng cơ sở. **Trạng thái:** lỗi nhất quán chắc chắn theo cách bảng hiện được mô tả; giá trị thay thế cần xác minh.

### A12 Cao — Chuẩn hóa độc lập từng tập con không phải quy trình test giữ độc lập

**Vị trí:** LA §3.2.2, P2287–P2290; §3.3.2, P3313; TT P385. **Trích:** “trong từng phần dữ liệu”; “dữ liệu trong từng tập con được chuẩn hóa độc lập”.

**Nhận xét:** Nếu fit Min–Max bằng toàn bộ test subset, đã sử dụng thống kê test và thay đổi phép biến đổi giữa train/test. Điều này cũng có thể xóa dịch chuyển biên độ cần đo trong hồi quy hoặc anomaly detection. P2290 lại mô tả extrema trên từng mẫu, khác với mô tả theo tập con. **Đề xuất:** ghi đúng code: fit scaler trên train của mỗi fold rồi transform validation/test; hoặc nếu chủ đích là chuẩn hóa từng cửa sổ, định nghĩa phép biến đổi và giới hạn ứng dụng đó. Không kết luận code rò rỉ khi chưa kiểm tra đúng phiên bản thí nghiệm; hiện phần mô tả chưa đủ tái lập. Chương 4 đã nêu fit trên pretrain, không áp dụng máy móc scaler Chương 4 để sửa số liệu Chương 3.

### A13 Cao — Thứ tự chia dữ liệu và tăng cường chưa thống nhất

**Vị trí:** LA P2291, P2569, P3246; TT P385. **Trích:** “gấp năm lần trong từng tập con”; “cửa sổ trượt ... trên các tập huấn luyện”.

**Nhận xét:** LA nói tăng cường cả từng tập con, TT nói chỉ tập huấn luyện. P2569 chỉ ghi chia ngẫu nhiên mà không nói group theo lần đo. **Đề xuất:** mô tả một pipeline duy nhất: xác lập run/exposure ID, chia group, fit preprocessing, tạo cửa sổ trong mỗi group; nêu riêng số cửa sổ train/validation/test và trọng số đánh giá. Nếu test chỉ lấy offset 0 như V3, không trình bày 5 offset test như mẫu độc lập. **Trạng thái:** cần đối chiếu code Chương 3; không khẳng định hai chương có cùng giao thức.

### A14 Vừa — Số thời điểm không chứng minh thời lượng chính xác

**Vị trí:** LA Bảng 3.1, P2312; §2.4.2, P1915. **Trích:** “429-430 (2*430 giây)” và chu kỳ “880 giây”.

**Nhận xét:** 430 × 2 = 860, khác 880 giây. V3 phân biệt chu kỳ được lập trình 880 s, interval cấu hình 2 s và số quan sát thực lưu. Số quan sát không phải timestamp. **Đề xuất:** tách ba thông tin; giữ 429–430 quan sát, interval danh định 2 s, chu kỳ lập trình 180 + 700 s; không chuyển trực tiếp 430 quan sát thành thời lượng chính xác. Với cửa sổ 64 mẫu, V3 nêu khoảng 128 s danh định và khoảng 131 s từ phép tính tổng hợp, không phải đo timestamp. **Nguồn:** Supplementary phần Physical timing.

### A15 Vừa — Nhãn “số mẫu ở từng tập con” NH₃/H₂ chưa chính xác

**Vị trí:** LA Bảng 3.1, P2322–P2324. **Trích số liệu:** 1.890 mẫu sau tăng cường, “Số mẫu ở từng tập con” = 378.

**Nhận xét:** 378 lần đo không chia đều thành 5 nhóm nguyên có cùng kích thước. Chia 75/76 lần đo rồi nhân 5 cửa sổ cho ra 375/380, không phải mỗi nhóm đúng 378. **Đề xuất:** ghi kích thước từng fold/group thực tế hoặc ghi “trung bình 378 cửa sổ/tập con” nếu đây chỉ là giá trị trung bình. Phân biệt số lần đo gốc với số cửa sổ.

### A16 Vừa — “Số phép đo độc lập” vượt bằng chứng

**Vị trí:** LA Bảng 3.1, P2301; mô tả dữ liệu và đánh giá. **Trích:** “Số phép đo độc lập”.

**Nhận xét:** Các run trong một recording CO liên tục và các định danh NH₃/H₂ chưa có day mapping không tự chứng minh độc lập thống kê hoặc acquisition session. **Đề xuất:** “Số nhóm/lần phơi khí được lưu” hoặc “Số run sau xử lý”; nêu riêng tiêu chí độc lập. **Nguồn:** V3 giới hạn independence và repeated predictions.

### A17 Cao — Ghép chuỗi đầu vào AE–LSTM chưa được giải thích

**Vị trí:** LA §3.2.3, P2442, đối chiếu P2231, P2286, P2572; TT P393. **Trích:** “Các ảnh được sắp xếp theo thứ tự thời gian”; “((batch, T, 256))”.

**Nhận xét:** Trước đó một ảnh chứa trọn cửa sổ một run và encoder sinh một vector 256 chiều. Để có T ảnh liên tiếp cần quy tắc tạo chuỗi, ánh xạ nhãn và group boundary. Chưa rõ T là các ảnh thật liên tiếp hay các tọa độ latent được reshape thành trục tuần tự. **Đề xuất:** nêu đúng tensor từ code, định nghĩa T, số ảnh/run, stride và nhãn đầu ra; không nối ảnh của các lần đo độc lập rồi gọi là động học thời gian. **Trạng thái:** cần xác minh phiên bản code sinh Bảng 3.4–3.5; chưa có căn cứ nói kiến trúc thực chạy chắc chắn sai.

### A18 Vừa — Bốn bộ dữ liệu bị kết luận thành ba

**Vị trí:** LA P2148, P4592; TT P833. **Trích:** “một bộ dữ liệu công khai (CO–Ethylene, trôi cảm biến)”; “một bộ dữ liệu công khai CO–Ethylene và hai bộ dữ liệu tự xây dựng”.

**Nhận xét:** §2.1 và Chương 4 sử dụng **hai công khai + hai tự thu thập**. **Đề xuất:** sửa P2148 thành “hai bộ dữ liệu công khai”; bổ sung drift vào kết luận cuối của cả hai bản và nêu vai trò benchmark drift khác với hỗn hợp hai khí.

### A19 Vừa — Sai khoảng năm thu thập drift

**Vị trí:** LA §2.3, P1488. **Trích:** “tháng 01/2007 đến tháng 02/2011, tương ứng với khoảng 36 tháng”.

**Nhận xét:** Mốc đầu sai; nguồn UCI ghi **01/2008**. **Đề xuất:** sửa năm 2007 thành 2008 và giữ cách mô tả “36 tháng” theo nguồn. **Nguồn:** [UCI drift](https://archive.ics.uci.edu/dataset/270/gas%2Bsensor%2Barray%2Bdrift%2Bdataset%2Bat%2Bdifferent%2Bconcentrations).

### A20 Vừa — Khoảng tháng của các batch đang trình bày như đo liên tục

**Vị trí:** LA Bảng 2.2, P1459, P1481, P1483; §4.5.7, P4423–P4424. **Trích:** “Phân vùng 8 và 9 ... tháng 21–30”.

**Nhận xét:** Tháng 21 là batch 7, không phải 8. UCI chỉ liệt kê tháng đo batch 2: 3,4,8,9,10; batch 9: 24,30; batch 10: 36. **Đề xuất:** phân biệt khoảng bao phủ với các tháng có đo; §4.5.7 sửa batch 8 = 22–23, batch 9 = 24 và 30. Nếu giữ “31–36” theo cách chia V3, ghi đó là khoảng phân vùng, không suy ra đã đo ở mọi tháng. **Nguồn:** UCI drift, Additional Variable Information.

### A21 Cao — Gán nguyên nhân kết quả cửa sổ muộn sai với pha đo

**Vị trí:** LA P4419–P4421. **Trích:** “do thông tin động học ... bị triệt tiêu khi cảm biến tiến vào trạng thái cân bằng hoặc bão hòa”; “toàn bộ thời gian tiếp xúc”.

**Nhận xét:** V3 xác định cửa sổ giữa/muộn chủ yếu nằm ở **pha hồi phục**, sau 180 s cấp khí; full-cycle gồm tiếp xúc **và** hồi phục. Các MAE không tự xác nhận cơ chế bão hòa hay triệt tiêu động học. **Đề xuất:** mô tả đúng vị trí index/pha đo; đổi full-cycle thành “toàn chu kỳ”; chỉ báo cáo sự phụ thuộc của sai số vào cửa sổ. Không suy ra nguyên nhân vật lý khi chưa có đo kiểm. **Nguồn:** Clean §V.F; Supplementary Physical timing.

### A22 Cao — Sai khác loss/MSD với quy tắc ngưỡng một phía

**Vị trí:** LA Công thức (16), P3286; quy tắc ở P3304. **Trích:** MSD là trung bình phần dư có dấu; “chỉ các sai số ... lớn hơn ngưỡng”.

**Nhận xét:** Công thức OMML hiện có dấu trị tuyệt đối ở |Ω|, nhưng không ở trung bình phần dư. Điểm MSD có thể âm; threshold phía trên không phát hiện dịch chuyển lớn theo hướng âm. **Đề xuất:** kiểm tra đúng định nghĩa được triển khai: nếu dùng |mean residual|, sửa công thức; nếu dùng signed mean, giải thích threshold hai phía hoặc lý do chỉ cần một phía. Không thay định nghĩa chỉ để khớp kết quả khi chưa kiểm tra code.

### A23 Vừa — Năm fold không phải năm đánh giá độc lập hoàn toàn

**Vị trí:** LA P3690; TT P556. **Trích:** “năm lần đánh giá chéo độc lập”.

**Nhận xét:** Các tập train trong 5-fold chồng lấn; nếu mỗi fold dùng lại toàn bộ 128 ảnh bất thường thì tập anomaly test cũng chồng lấn. **Đề xuất:** “năm fold xác thực chéo ở cấp lần đo”; báo cáo chính xác anomaly nào nằm trong từng fold và SD giữa fold, không coi là năm acquisition độc lập.

### A24 Vừa — 64 bất thường: năm hay sáu nhóm

**Vị trí:** LA §3.3.2, P3308 và P3311. **Trích:** “64 sự kiện thuộc sáu nhóm”; “Được chia vào 5 loại”.

**Nhận xét:** Danh sách sáu nhóm có thêm **lỗi cảm biến**, danh sách năm nhóm không có. **Đề xuất:** thống nhất taxonomy, số lượng mỗi nhóm, cách gán nhiều nhãn và sự khác nhau giữa event/run với ảnh sau tăng cường. Không coi 128 cửa sổ là 128 sự kiện độc lập.

### A25 Vừa — 452 lần đo bị đổi thành 452 tổ hợp nồng độ

**Vị trí:** TT P368, đối chiếu LA P2112 và Bảng 2.5. **Trích:** “tạo thành 452 tổ hợp hỗn hợp”.

**Nhận xét:** LA gọi đây là **452 lần đo**, có các lần lặp. Số lần đo khác số tổ hợp duy nhất. **Đề xuất:** “452 lần đo thuộc 7 lớp thành phần khí, tương ứng 42.940 quan sát theo thời gian”; chỉ ghi số tổ hợp duy nhất nếu đã đếm từ các tọa độ nồng độ.

### A26 Vừa — Độ ẩm VOCs cần nguồn riêng

**Vị trí:** LA P2137 và P4596; TT P837. **Trích:** “được duy trì ổn định với nhiệt độ 25 °C, ... RH 82%”.

**Nhận xét:** Xác nhận không đo môi trường ở V3 áp dụng NH₃/H₂, không đủ căn cứ suy sang VOCs. Nhưng bản thảo cũng chưa chỉ nguồn thiết bị/log cho VOCs. **Đề xuất:** dẫn mô tả thực nghiệm VOCs hoặc log đo/kiểm soát; nếu không có, hạ mức khẳng định. Kết luận “các điều kiện thí nghiệm có kiểm soát” cần nói rõ thông số nào được kiểm soát, tránh bao gồm nhiệt độ/độ ẩm NH₃/H₂.

### A27 Vừa — Loại toàn bộ nồng độ 0 không được mô tả đúng

**Vị trí:** TT P385; LA P2234. **Trích TT:** “loại bỏ ... các mẫu có nồng độ khí bằng 0”.

**Nhận xét:** LA chỉ loại mẫu **cả hai khí cùng bằng 0**. Cách viết TT có thể hiểu loại luôn mẫu đơn khí như (0,c), (c,0). **Đề xuất:** “loại các mẫu có đồng thời CO = 0 và C₂H₄ = 0” nếu đúng code; không áp dụng tiêu chí này cho mọi bộ dữ liệu. Mẫu không khí nền có thông tin cho false positive/low-end calibration; không nên nói chúng hoàn toàn vô ích.

### A28 Vừa — 1 Hz bị áp dụng chung cho NH₃/H₂

**Vị trí:** LA P2286. **Trích:** “đưa tần số lấy mẫu về 1 Hz”.

**Nhận xét:** NH₃/H₂ có interval cấu hình 2 s, tức cadence danh định khoảng 0,5 Hz. Đoạn đang nói chung cả hai bộ dữ liệu nhưng không giải thích nội suy hay resampling. **Đề xuất:** tách preprocessing CO (100 Hz → 1 Hz nếu đúng code) và NH₃/H₂; nếu nội suy NH₃/H₂, nêu phương pháp và không gọi đó là đo thực ở 1 Hz. **Nguồn đối chiếu NH₃/H₂:** V3 author confirmations.

## B Diễn đạt chuyên môn và kết luận

### B01 Vừa — Xếp NO₂, CO, NH₃ vào VOCs

**Vị trí:** LA §1.4.1, P911. **Trích:** “các hợp chất VOCs như hương rượu, NO2, CO và NH3”.

**Nhận xét:** NO₂, CO và NH₃ không phải hợp chất hữu cơ dễ bay hơi; “hương rượu” cũng không là tên một hợp chất. **Đề xuất:** “các VOC như ethanol và các khí vô cơ như NO₂, CO, NH₃”. TT P222 cũng nên tách “khí độc”, “khí dễ cháy” và VOCs, tránh xếp H₂ mặc nhiên là khí độc.

### B02 Vừa — CatBoost bị gọi là học sâu

**Vị trí:** LA P1364. **Trích:** “các thuật toán học sâu như Transformer, ResNet, MobileNet và CatBoost”.

**Nhận xét:** CatBoost là gradient boosting trên cây quyết định. **Đề xuất:** tách các kiến trúc mạng học sâu và các mô hình boosting; không dùng một danh mục sai để lập luận mọi phương pháp đều tự học đặc trưng như deep networks. **Nguồn:** [CatBoost documentation](https://catboost.ai/docs/en/).

### B03 Vừa — Z-score không robust trước ngoại lai

**Vị trí:** LA P1089. **Trích:** “Chuẩn hóa Z-score phù hợp khi dữ liệu có ngoại lai”.

**Nhận xét:** Mean/std bị ngoại lai chi phối. **Đề xuất:** “Z-score phù hợp khi cần chuẩn hóa mean/std; khi có ngoại lai mạnh, cân nhắc robust scaling bằng median và khoảng phân vị”. Không khẳng định chuẩn hóa nào luôn cải thiện độ chính xác. **Nguồn:** [StandardScaler documentation](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).

### B04 Vừa — Hấp thụ và hấp phụ dùng lẫn

**Vị trí:** LA P898. **Trích:** “khi khí được hấp thụ”.

**Nhận xét:** Trong đoạn nói cơ chế tương tác **bề mặt** MOX, thuật ngữ phù hợp là “hấp phụ” và phản ứng bề mặt. **Đề xuất:** sửa từ, đồng bộ “hấp phụ–giải hấp” với các mục sau; không giản lược mọi thay đổi điện trở thành hấp phụ thuần túy.

### B05 Vừa — Tái tạo Autoencoder không đảm bảo khử nhiễu hoặc tránh quá khớp

**Vị trí:** LA P2364, P2440, P2572, P2578; TT P381, P393. **Trích:** “tránh hiện tượng học thuộc dữ liệu”; “Nhiễu ... được giảm thiểu”.

**Nhận xét:** AE tái tạo input thông thường có thể học cả nhiễu và học thuộc. Reconstruction loss thấp không chứng minh latent hữu ích cho hồi quy. **Đề xuất:** dùng “học biểu diễn nén”; chỉ khẳng định khử nhiễu nếu có denoising objective hoặc kiểm chứng trên noise controls; dùng kết quả hồi quy held-out để chứng minh hiệu quả downstream.

### B06 Vừa — Gán chức năng vật lý cho từng lớp LSTM khi chưa kiểm chứng

**Vị trí:** LA P2443. **Trích:** “lớp thứ nhất ... ngắn hạn”; “lớp thứ hai ... dài hạn ... tương tác giữa các thành phần khí”.

**Nhận xét:** LSTM xếp chồng không mặc nhiên phân chia chức năng theo thứ tự lớp như vậy. **Đề xuất:** mô tả hai lớp học biểu diễn tuần tự nhiều mức; nếu muốn gán vai trò động học, cần phân tích/ablation tương ứng. Liên hệ với việc định nghĩa trục tuần tự ở A17.

### B07 Vừa — Ảnh tái tạo không phải vector latent

**Vị trí:** LA P2364. **Trích:** “ảnh đặc trưng được tái tạo ... là biểu diễn tiềm ẩn”.

**Nhận xét:** Latent là output encoder, ảnh tái tạo là output decoder. **Đề xuất:** phân biệt ảnh input, latent 256 chiều và ảnh reconstruction; xác định LSTM nhận latent hay ảnh để tránh mâu thuẫn kiến trúc.

### B08 Cao — Biểu diễn ảnh không tự loại bỏ mọi rò rỉ dữ liệu

**Vị trí:** LA P2231, P2291, P3246. **Trích:** “loại bỏ khả năng xảy ra rò rỉ dữ liệu”.

**Nhận xét:** Gom một lần đo thành ảnh chỉ giải quyết một nguồn leakage nếu chia đúng group; vẫn có thể rò rỉ ở scaler, filtering qua ranh giới group, cửa sổ chồng lấn, selection hoặc checkpoint. **Đề xuất:** “giảm nguy cơ rò rỉ do các quan sát cùng lần đo được giữ trong một nhóm”; chứng minh từng bước bằng protocol/audit, không bảo đảm tuyệt đối từ định dạng ảnh.

### B09 Vừa — MAE phần trăm và ppm ở các khí khác thang không so trực tiếp

**Vị trí:** LA P3244 và các câu xếp CO là khí “khó nhất”; TT P782. **Trích:** “RMSE = 23.56 ... CO ... chỉ đạt RMSE = 1.03 ... Ethylene”.

**Nhận xét:** CO và ethylene có dải nồng độ khác nhau. Sai số ppm lớn hơn không tự chứng minh nhiệm vụ khó hơn. **Đề xuất:** đối chiếu NMAE/NRMSE theo dải hoặc R² trên cùng protocol; giữ ppm để diễn giải ứng dụng, không dùng “chỉ đạt” cho sai số thấp hơn.

### B10 Vừa — CDF phân vị 90 không bảo đảm sai số cực trị trong giới hạn cho phép

**Vị trí:** LA P2910. **Trích:** “đảm bảo ... sai số cực trị ... được kiểm soát trong giới hạn cho phép”.

**Nhận xét:** Q₀.₉ cho biết 90% sai số ở dưới một mức; không ràng buộc 10% còn lại, không là bảo đảm coverage mới và chưa có tiêu chí sai số chấp nhận được. **Đề xuất:** “trên tập kiểm tra quan sát, 90% sai số tuyệt đối không vượt ...”; nêu thêm max/Q₀.₉₉ nếu muốn bàn cực trị, và nguồn tiêu chí ứng dụng nếu có.

### B11 Vừa — Q₀.₉ không phải sai số của toàn bộ 10% trường hợp tệ nhất

**Vị trí:** LA P4507. **Trích:** “đại diện cho sai số ở 10% kịch bản dự đoán tệ nhất”.

**Nhận xét:** Đây là ngưỡng phân vị, không phải trung bình tail (CVaR) hoặc max. **Đề xuất:** “ngưỡng sai số tuyệt đối mà khoảng 90% mẫu không vượt quá”; thống nhất ký hiệu Q₀.₉ và đơn vị ppm.

### B12 Cao — Lợi thế trung bình với năm cặp nhãn bị diễn giải thành lợi ích ổn định

**Vị trí:** LA P4319; TT P827. **Trích:** “Fine-tuned luôn nhất quán đạt hiệu năng tốt hơn ... bất kể chiến lược chọn mẫu”.

**Nhận xét:** Với NH₃ K=5, farthest-point Scratch 86,39 và Fine-tuned 86,02 có chênh lệch rất nhỏ, SD lớn. Tuyên bố “ổn định ... chính xác” cần khoảng bắt cặp; không được suy từ mean thấp hơn chút ít. **Đề xuất:** nêu NH₃ là ngoại lệ yếu nhất ở K=5; phân biệt xu hướng trung bình và bằng chứng thống kê, chỉ giữ lợi ích rõ khi được số liệu/interval hỗ trợ. **Nguồn:** Clean §V.C–D, §VI.

### B13 Vừa — “Chiến lược phù hợp nhất từng khí” trái fine-tuning xác định trước

**Vị trí:** LA P4578 đối chiếu P3816. **Trích:** “sử dụng chiến lược chuyển giao phù hợp nhất với từng khí mục tiêu”.

**Nhận xét:** V3 định trước fine-tuning cho mọi khí, không chọn policy bằng test. **Đề xuất:** “sử dụng chính sách fine-tuning được xác định trước cho tất cả các khí”. Nếu bàn best observed policy, ghi riêng thăm dò và không dùng để tạo headline gain.

### B14 Vừa — Ablation không chứng minh cơ chế hóa lý

**Vị trí:** LA P4392, P4579. **Trích:** “phụ thuộc chặt chẽ vào đặc tính phản hồi hóa lý riêng biệt”.

**Nhận xét:** Bảng đo tương phản conditional qua seeds, nhiều SD lớn. V3 không xác nhận cơ chế vật lý từ các hiệu ứng này; CO sensor-ID CI bổ sung còn chứa 0. **Đề xuất:** báo cáo tác động theo gas/budget trong protocol; tách giả thuyết cơ chế khỏi kết quả đã kiểm chứng, dẫn Supplementary S10 nếu bàn CO. “Không có một nghiên cứu cắt bỏ ... mang lại lợi ích” nên đổi thành “không có thành phần nào thể hiện lợi ích đồng nhất”.

### B15 Vừa — Gọi H₂ là lợi ích thành phần rõ nhất chưa thống nhất bảng

**Vị trí:** LA P4579 so với P4392 và Bảng 4.7. **Trích:** “lợi ích thể hiện rõ nhất đối với H2”; “NH3, CO và C2H4 ... chưa đủ nhất quán”.

**Nhận xét:** Phần trước nhấn mạnh CO (attention +10,27 ppm) nhưng đoạn kết luận chuyển sang H₂ mà không nêu tiêu chí “rõ nhất”. **Đề xuất:** mô tả từng thành phần/khí và CI tương ứng; không gộp thứ hạng mean, SD và significance thành một nhận định bao quát.

### B16 Vừa — Gán mức độ và nguyên nhân drift chỉ từ thời gian

**Vị trí:** LA P4423. **Trích:** “trôi ... trung bình”; “rất nghiêm trọng ... lão hóa vật lý và suy giảm hóa học”.

**Nhận xét:** Thời điểm và MAE lớn không tách được drift khỏi thay đổi phân bố nồng độ hoặc nguyên nhân hóa học. **Đề xuất:** “batch 10 cho sai số cao và lợi ích transfer chưa rõ”; chỉ gán mức drift/aging nếu có chỉ số drift hoặc đo vật lý độc lập. Giữ các normalized-error, constant và loss controls như V3.

### B17 Vừa — Loss hội tụ không chứng minh độ chính xác concentration hoặc anomaly

**Vị trí:** LA P3549, P3922; TT P650. **Trích:** “đạt độ chính xác dự đoán cao”; “học được biểu diễn ổn định”.

**Nhận xét:** Hình loss chỉ chứng minh xu hướng tối ưu reconstruction trong thang dữ liệu tương ứng. **Đề xuất:** “loss tái tạo giảm và độ biến động giữa seeds nhỏ”; dùng bảng held-out MAE/F1 để bàn độ chính xác. Không so loss giữa ba bộ dữ liệu như cùng đơn vị nồng độ. **Nguồn:** Clean §V.A.

### B18 Vừa — Suy độ tin cậy/tái lập cao từ scatter nhiều seed

**Vị trí:** LA P4053; TT P782. **Trích:** “đã khẳng định ... khả năng tái lập và độ tin cậy cao”.

**Nhận xét:** Nhiều dự đoán trên cùng exposures không là acquisition độc lập; scatter bám y=x chỉ hỗ trợ mô tả sai số. **Đề xuất:** dùng “xu hướng quan sát được qua 10 seed trong cùng protocol”; báo cáo paired statistics và các giới hạn day/environment/device.

### B19 Vừa — “Ngưỡng thích nghi” chưa được định nghĩa

**Vị trí:** LA P662, P670, P677 so với P3304. **Trích:** “ngưỡng thích nghi”.

**Nhận xét:** Phương pháp được mô tả là phân vị 95% của validation normal, cố định khi test. Chưa có cơ chế cập nhật online hoặc thích nghi khi drift. **Đề xuất:** “ngưỡng xác định từ dữ liệu xác thực bình thường”; chỉ dùng adaptive khi chỉ rõ quy tắc cập nhật và kiểm soát contamination.

### B20 Vừa — Các khẳng định về tiết kiệm chi phí và IAQ vượt đánh giá

**Vị trí:** LA P3755, P4580, P665–P666; TT P224, P834. **Trích:** “tối ưu chi phí hiệu chuẩn đáng kể”; “khắc phục triệt để”.

**Nhận xét:** V3 là label withholding trên dữ liệu đã có nồng độ, không đo cost acquisition của pool chưa định lượng, chưa đánh giá chuyển thiết bị hoặc ambient low-ppm. **Đề xuất:** giữ kết luận “hỗ trợ hiệu quả nhãn trong cùng hệ thống”; trình bày IAQ là hướng ứng dụng, chi phí thực nghiệm và triển khai là future work. Thay “triệt để” bằng “nghiên cứu giải quyết”. **Nguồn:** Clean §I, §VI.

### B21 Vừa — R² cao không tự chứng minh khái quát hóa

**Vị trí:** LA P2960. **Trích:** “R2 càng gần 1 thì ... mức độ khái quát ... càng cao”.

**Nhận xét:** R² phản ánh sai số tương đối so với phương sai trên tập đang đánh giá. Khả năng khái quát phụ thuộc test protocol và phân bố, không được bảo đảm chỉ bằng R². **Đề xuất:** “R² cao trên tập kiểm tra độc lập phản ánh mức phù hợp tốt trong thiết lập đánh giá đó”; bổ sung rằng R² có thể âm và cần MAE/RMSE.

### B22 Vừa — Suy Recall từ CDF sai phép trừ

**Vị trí:** LA P3555. **Trích:** “CDF ... khoảng 0.08–0.10, nghĩa là khoảng 90–94%”.

**Nhận xét:** 1 − (0,08 đến 0,10) = **90–92%**, không phải 90–94%. **Đề xuất:** sửa khoảng hoặc đọc lại CDF; ưu tiên con số tính trực tiếp từ confusion matrix, Recall abnormal = 116/128 = 90,625% ở bảng minh họa đó.

### B23 Vừa — Recall anomaly thực và synthetic chưa được phân tách

**Vị trí:** LA P3308, P3566, P3690; TT phần §3.3. **Trích:** “bất thường thực tế ... và ... tổng hợp”; 308 mẫu test.

**Nhận xét:** Chưa rõ bảng/confusion matrix dùng 128 cửa sổ từ 64 sự kiện thật hay trộn synthetic; cũng chưa rõ bảng một split khác thế nào với mean 5-fold. **Đề xuất:** ghi composition test, cách chia event, kết quả real/synthetic riêng và nhãn “một fold minh họa” cho Bảng 3.7–3.8 nếu đúng. Không so F1 0,94 của một split với 0,91 ± 0,05 như cùng estimand. **Trạng thái:** thiếu thông tin, cần xác minh.

## C Tham chiếu và trình bày hiển nhiên

### C01 Cao — Trích sai dataset drift

**Vị trí:** LA §2.3, P1435. **Trích:** “J. Fonollosa, ‘Gas sensor array under dynamic gas mixtures’ ... 10.24432/C5WP4C”.

**Nhận xét:** Đây là nguồn dynamic mixtures, không phải drift. **Đề xuất:** thay bằng **A. Vergara, Gas Sensor Array Drift at Different Concentrations, DOI 10.24432/C5MK6M** và các paper drift/calibration liên quan. Nguồn dataset phải khớp số 13.910 records, 128 descriptors. **Nguồn:** Clean reference [16]; [UCI drift](https://archive.ics.uci.edu/dataset/270/gas%2Bsensor%2Barray%2Bdrift%2Bdataset%2Bat%2Bdifferent%2Bconcentrations).

### C02 Vừa — Đảo số tài liệu M-Training và M-S4VMs

**Vị trí:** LA §4.2, P3736; TLTK [88], [89]. **Trích:** “M-Training [88] và M-S4VMs [89]”.

**Nhận xét:** [88] là M-S4VMs, [89] là M-Training. **Đề xuất:** “M-Training [89] và M-S4VMs [88]”.

### C03 Vừa — TDACNN dẫn nhầm bài parameter-feature transfer

**Vị trí:** LA P3738; TLTK [91] P4725. **Trích:** “TDACNN [91]”.

**Nhận xét:** [91] là bài Xia về parameter-feature transfer, không phải TDACNN. **Đề xuất:** bổ sung nguồn TDACNN của Y. Zhang et al., DOI **10.1016/j.snb.2022.131739** từ V3 rồi cập nhật số trích dẫn; không thay tên phương pháp để giữ số tài liệu sai.

### C04 Vừa — Số bài CEGNN không khớp V3

**Vị trí:** LA TLTK [64], P4698. **Trích:** “vol. 445 ... p. 530004”.

**Nhận xét:** V3 ghi **Art. no. 138470**, DOI **10.1016/j.snb.2025.138470**. Tựa hiện còn lẫn tên journal vào title. **Đề xuất:** đối chiếu publisher metadata và cập nhật đồng bộ title, journal, article number và DOI; không giữ p. 530004 khi không có nguồn. **Nguồn đối chiếu:** Clean reference [6].

### C05 Vừa — DOI [P1] đang là DOI cả sách

**Vị trí:** LA P2152, P4610; TT P843. **Trích:** “10.1007/978-3-031-93816-0”.

**Nhận xét:** V3 dẫn chương pp.85–92 bằng DOI có hậu tố **_11**. **Đề xuất:** dùng **10.1007/978-3-031-93816-0_11** cho bài/chương cụ thể; ISBN và DOI sách có thể giữ riêng, không thay DOI chương. **Nguồn:** Clean reference [28]; V3 hardware source note.

### C06 Vừa — Năm của [P5] không khớp thông tin volume/issue

**Vị trí:** LA P4614 và phần công trình Chương 3; TT P847. **Trích:** “vol. 26, no. 3, pp. 4739–4748, 2025”.

**Nhận xét:** V3 ghi volume/issue này là **Feb. 2026**. “2025” trong DOI hoặc early access không tự là năm của số tạp chí. **Đề xuất:** dùng năm 2026 nếu dẫn bản volume/issue; nếu muốn ghi early access 2025, ghi rõ và thống nhất bibliographic form. **Nguồn đối chiếu:** Clean reference [30].

### C07 Vừa — Trang [P9] mâu thuẫn DOI

**Vị trí:** LA P4618; TT P851. **Trích:** “112. 164-171” và DOI kết thúc “112.2026.126-134”.

**Nhận xét:** Có hai dải trang khác nhau trong cùng trích dẫn. **Đề xuất:** kiểm tra bài trên journal để xác định trang; không lấy chuỗi DOI làm bằng chứng tuyệt đối rằng trang phải là 126–134. Chuẩn hóa số tập/số và pp. **Trạng thái:** cần xác minh; DOI chưa truy cập thành công trong lần rà soát này.

### C08 Vừa — Bài đang review nằm trong “đã công bố”

**Vị trí:** LA P4582–P4583, P4608–P4620; TT P842–P853. **Trích:** “được công bố”; “Third--round review”.

**Nhận xét:** “Đang phản biện” không đồng nghĩa đã công bố. **Đề xuất:** tách danh mục đã công bố và đang phản biện; ghi tên journal **IEEE Sensors Journal** đúng theo V3, dùng tựa bản V3 hiện tại nếu đây là cùng manuscript. Không tự cập nhật acceptance khi chưa có bằng chứng. Các Q/IF cần năm và nguồn nếu yêu cầu đưa vào danh mục.

### C09 Vừa — Năm hội nghị và năm bản proceedings bị trộn

**Vị trí:** LA TLTK [94]–[96], P4728–P4730. **Trích:** ICLR 2023 nhưng “Nov. 2022”; KDD nhưng “Oct. 2020”; AAAI 2022 nhưng “Jun. 2021”.

**Nhận xét:** Các mốc sau có thể là ngày preprint. **Đề xuất:** khi dẫn bản proceedings dùng ICLR **2023**, KDD **2021**, AAAI **2022** theo V3; nếu dẫn preprint thì ghi arXiv và năm preprint riêng. Cần kiểm tra metadata chính thức trước khi hoàn thiện.

### C10 Vừa — Tựa tài liệu bị lặp hoặc lẫn tên nguồn

**Vị trí:** LA [62] P4696, [64] P4698, [83] P4717, [100] P4734, [104] P4738. **Trích:** “Journal of Food Composition and Analysis Rapid detection”; tựa [83] lặp hai lần; “Stat. Comput. 2004 143”.

**Nhận xét:** Dấu hiệu copy metadata chưa làm sạch. **Đề xuất:** loại journal khỏi trường title, giữ tựa [83] một lần; chuẩn hóa journal/volume/issue/pages/DOI. [104] đang dùng DOI URL làm tên nguồn, nên điền **Annals of Statistics** theo V3. [82] còn thiếu năm, journal/venue và DOI; cần bổ sung từ nguồn chính thức.

### C11 Vừa — Trích sai lĩnh vực làm bằng chứng trực tiếp cho E-nose

**Vị trí:** LA P2187 dẫn [77] P4711; P3293 dẫn [84]–[86]; TLTK [87] P4721.

**Nhận xét:** [77], [84] về gas turbine, [85] về subsurface fluids, [86] về electric grid; không mặc nhiên chứng minh các chức năng MSE/MADn/MSD trên E-nose. [87] có title/author/venue/DOI cần kiểm tra khớp metadata. **Đề xuất:** nêu đây là phương pháp dùng trong lĩnh vực liên quan, bổ sung chứng cứ E-nose hoặc hạ khẳng định; kiểm tra từng nguồn trước khi gán khả năng cụ thể cho độ đo.

### C12 Vừa — Công thức đánh số lặp và tham chiếu sai

**Vị trí:** LA §4.3, P3757, P3764, P3787–P3814; §3.3 P3254–P3303.

**Nhận xét:** §4.3.2 có (20)–(23), §4.3.3 có (24)–(25), §4.3.4 có (26); §4.3.5 lại quay về **(23), (24), (25)** và §4.3.6 dùng lại (26). P3757 dẫn (1) cho X nhưng phương trình bên dưới là (20); target y là (21), không phải (20). A_K ở (22), không phải (21). Chương 3 cũng tái sử dụng số (7)–(19) giữa hai bài toán. **Đề xuất:** đánh số thống nhất theo chương như (3.1), (4.1), dùng cross-reference Word và cập nhật mọi câu dẫn. Không chỉ sửa riêng label vì tham chiếu sẽ tiếp tục sai.

### C13 Vừa — Kích thước ma trận phản hồi không khớp cách viết

**Vị trí:** LA Công thức (2), P2215.

**Nhận xét:** Ma trận hiển thị hàng là thời điểm, cột là cảm biến nhưng ghi không gian **k × (Tstable+1)**. **Đề xuất:** đổi không gian thành **(Tstable+1) × k**, hoặc chuyển vị ma trận để khớp sensor × time. Thống nhất T/Tstable ở hàng cuối và phân biệt số bước thời gian với thời lượng vật lý.

### C14 Vừa — Thiếu denominator guard so với công thức V3

**Vị trí:** LA Công thức (29), P3809. **Trích mẫu số thứ hai:** “∑M”.

**Nhận xét:** V3 dùng **max(1, ∑M)** ở cả term visible và masked. Với raw mask hiện tại visible entries luôn còn nên thiếu guard không đổi loss trong protocol này; tuy nhiên công thức không phản ánh đầy đủ triển khai V3. **Đề xuất:** thêm guard và ghi điều kiện mask; không diễn giải đây là nguyên nhân làm kết quả số liệu sai. **Nguồn:** Clean Equation (14) và giải thích sau phương trình.

### C15 Nhẹ — Ký hiệu Z dùng hai vai trò

**Vị trí:** LA P3788, P3800, P3805. **Trích:** Zᵢ là token matrix và Z_bks là Bernoulli participation.

**Nhận xét:** Không nhất thiết sai toán nhưng dễ nhầm với representation Z. **Đề xuất:** dùng **B_bks** cho participation như V3 và định nghĩa b,t,s,k, vị trí bắt đầu span, ba spans, xác suất 0,45. Đừng mô tả span luôn che tất cả kênh: P3749 hiện ghi như vậy, trong khi mask là participation riêng từng kênh.

### C16 Vừa — Tham chiếu bảng/hình sai hoặc bỏ đối tượng khỏi TT

**Vị trí:** TT P546, P825, P555–P556, P650–P654. **Trích:** “Khung phương pháp Hình 3.2”; “Bảng 4.6”.

**Nhận xét:** Khung anomaly là **Hình 3.12**, không phải 3.2 (AE–LSTM). Bảng baseline ngay trước P825 thiếu caption “Bảng 4.6”. Hình 4.3/caption đặt sau tiêu đề §4.3.2 nhưng là nội dung §4.3.1. **Đề xuất:** sửa tham chiếu, thêm caption và sắp xếp hình sát nội dung; giữ số kế thừa LA nếu chủ ý, không bắt buộc đánh lại toàn bộ. Nếu bỏ Bảng 4.1/4.4/... trong TT, cần tránh tham chiếu tới bảng không có trong bản tóm tắt.

### C17 Nhẹ — Chú thích tiếng Anh sót ở nhiều hình Chương 3

**Vị trí:** LA P2260, P2402, P2605, P2691, P2740, P2790, P2839, P2886, P3341, P3521. **Trích:** “Fig. 3. Regression process of mixed-gas concentration using Autoencoder–LSTM”.

**Nhận xét:** Cùng một chú thích xuất hiện dưới các hình smoothing, reconstruction, learning curves, CDF và anomaly, không khớp nội dung. **Đề xuất:** xóa caption tiếng Anh sót hoặc dịch đúng caption riêng từng hình. Đây là caption thừa trong textboxes/cấu trúc tài liệu; kiểm tra trực quan vị trí Word trước khi xóa, không xóa hình chính.

### C18 Nhẹ — Ký hiệu hóa học và số thập phân chưa thống nhất

**Vị trí:** cả LA và TT; Bảng 4.3/4.6, danh mục viết tắt, headings. **Ví dụ:** “NH3”, “NH₃”, “H2”, “H₂”, “C2H4”, “C₂H₄”; “82,85 ± 31,89” xen “86.39 ± 36.11”; “25,57” xen “47.45”.

**Nhận xét:** Nên thống nhất chỉ số dưới hóa học và một quy ước decimal/thousands cho bảng tiếng Việt. **Đề xuất:** chọn dấu phẩy thập phân hoặc dấu chấm thập phân theo quy định, áp dụng đồng bộ; ghi ppm trong header, chọn số chữ số có nghĩa theo từng target. Thống nhất ethylene/etylen, seed/Seed/Seeds, fine-tuned/Fine-Tuned.

### C19 Nhẹ — Năm ở danh mục “đã công bố” và thông tin bibliographic cần rà soát riêng

**Vị trí:** LA P1385 vs P4615; TT P848. **Trích:** Sensor Review ISSN “1758-6828” vs “0260-2288”.

**Nhận xét:** Hai mã có thể là eISSN và print ISSN, không nên coi mặc nhiên là số sai. **Đề xuất:** ghi nhãn eISSN/ISSN hoặc chọn quy ước thống nhất. Phân biệt năm hội nghị 2025 và proceedings 2026 ở SOICT/REV-ECIT; không sửa năm chỉ theo tên sự kiện.

## D Chính tả viết thiếu và câu chưa hoàn chỉnh

| Mã | Vị trí và trích đoạn | Nhận xét và đề xuất |
| --- | --- | --- |
| D01 | TT P227, P278: “mũi điện” | Thiếu “tử”; sửa thành “mũi điện tử”. |
| D02 | TT P230: “- Pháp phát hiện bất thường” | Viết thiếu. Sửa “- Phát triển phương pháp phát hiện bất thường từ dữ liệu mũi điện tử.” |
| D03 | TT P237: “môi trường không khí trong nhà, hỗn hợp của chúng” | “chúng” không có antecedent rõ. Sửa “Tập trung vào các khí ... và hỗn hợp của chúng trong bối cảnh ...”. |
| D04 | TT P289: “các mô hình mô hình dự báo” | Lặp từ; bỏ một “mô hình”. |
| D05 | TT P830–P831: “Kết luận” liên tiếp | Heading lặp; giữ một. |
| D06 | LA P4599; TT P840: “các thiết bị các thiết bị độc lập” | Lặp cụm và cả câu chưa có vị ngữ. Sửa “Các vấn đề như học liên tục, chuyển giao giữa các thiết bị độc lập, ... vẫn cần được nghiên cứu.” |
| D07 | LA P1901: “đảm báo đúng tỷ lệ” | “đảm báo” → “đảm bảo”. |
| D08 | LA P1925: “Bộ dự liệu” | “dự liệu” → “dữ liệu”. |
| D09 | LA Bảng 1.2, P923: “Bộ dư liệu café rang” | “dư liệu” → “dữ liệu”; thống nhất cách viết “cà phê rang”. |
| D10 | LA P1063: “đóng vai trò trong E-nose chốt” | Câu hỏng. Sửa “đóng vai trò then chốt trong nghiên cứu E-nose”. |
| D11 | LA P2210: “(1≤i≤M” | Thiếu ngoặc đóng; thêm “)”. P2211 dùng D thay cho Dᵢ, cần thống nhất. |
| D12 | LA P2218: “thời điểm ttt” | “ttt” → “t”. |
| D13 | LA P2362: “để học để học” | Lặp từ; giữ “để học”. |
| D14 | LA P3290: “tập tất cả tập hợp tất cả” | Sửa “tập hợp tất cả các vị trí không gian (i,j)”. |
| D15 | LA P3292: “k=1.4826.” | Dấu chấm nằm giữa công thức và “là”; sửa “k = 1,4826 là ...” theo quy ước số đã chọn. |
| D16 | LA P3426: “mô hinh” | “mô hinh” → “mô hình”. |
| D17 | LA P4050: “Ở ngân sách Bảng 4.3 báo cáo” | Câu thiếu thành phần. Sửa “Bảng 4.3 báo cáo kết quả tại các mức ngân sách ...”. |
| D18 | LA P3760: “Trong đó là T là” | Sửa “Trong đó, T là ...”. P3761 có câu cụt “Vectơ nồng độ mục tiêu hai chiều”; ghép vào câu định nghĩa yᵢ. |
| D19 | LA P3826: “để là tập thích nghi” | Sửa “làm tập thích nghi”. |
| D20 | LA P3836: “thích nghi.Do” | Thiếu khoảng trắng; sửa “thích nghi. Do ...”; nên tách hai ý protocol và masking thành hai đoạn. |
| D21 | LA P3736: “[95]và” | Thiếu khoảng trắng: “[95] và”. |
| D22 | LA P3782: “cảm biến,es” | Thiếu khoảng trắng và dấu câu: “cảm biến eₛ.” |
| D23 | LA P3952: “qua 6-fold (tương ứng ...; tập CO...” | Ngoặc mở chưa đóng trước dấu chấm phẩy. Đóng sau “qua các seed)”; viết câu CO riêng. |
| D24 | LA P4507: “nâng cao hệ số R2 (đạt cao nhất ... 0.935, đồng thời” | Thiếu ngoặc đóng; thêm sau 0,935, kiểm tra lại độ dài câu. |
| D25 | LA P4321: “(PLSR ... còn Extra Trees ... CO.” | Thiếu ngoặc đóng; thêm “)” hoặc tách thành câu độc lập. Đồng thời sửa kết luận số liệu ở A10. |
| D26 | LA P4577: “Ethylene.Những” | Thiếu khoảng trắng sau dấu chấm. |
| D27 | LA P4505: “... khác nhau. kiểm thử ...” | “kiểm thử” bắt đầu câu nhưng viết thường và thiếu chủ ngữ. Sửa “Nghiên cứu kiểm tra các phương án thay thế ...”. |
| D28 | LA P4482: “Dải nồng độ lịch sử cố định ... và đánh trọng số...” | Câu thiếu chủ ngữ/vị ngữ hoàn chỉnh. Sửa “NMAE sử dụng dải nồng độ lịch sử cố định ... và gán trọng số bằng nhau cho các khí.” |
| D29 | LA Bảng 3.9, P3627; TT P613: “Local Outliner Factor” | Tên đúng **Local Outlier Factor**. Sửa mọi bảng và mô tả. |
| D30 | TT Bảng 3.4, P453: “AE-XGBoots” | Tên sai; sửa **AE–XGBoost**. Cả hai occurrence trong XML choice/fallback cần giữ đồng bộ khi chỉnh Word. |
| D31 | LA P1384/P4612: “... Noses”, ”, MMMS2024” | Dư dấu ngoặc kép và dấu phẩy; xóa phần “”, ”,” thừa. |
| D32 | TT P850: “REV-ECIT 2025, , ISBN” | Dư một dấu phẩy. “Xgboost” trong tiêu đề: đối chiếu tựa đã công bố trước khi chuẩn hóa thành XGBoost. |
| D33 | LA P2148: “bao gồm một bộ dữ liệu công khai (CO–Ethylene, trôi cảm biến)” | Ngoài lỗi số lượng ở A18, dấu ngoặc đang gộp hai bộ thành một. Viết thành danh sách hai bộ rõ ràng. |
| D34 | LA P241–P245: “em” xen “Tôi” | Đại từ chưa thống nhất trong lời cảm ơn. Chọn “tôi” hoặc “em” theo giọng văn và quy định luận án rồi áp dụng đồng bộ. |
| D35 | LA danh mục, P400, P442 | **GELU:** “Gaussian Error Linear Unit” → **Gaussian Error Linear Units** theo tên gốc; cột tiếng Anh NH₃ đang ghi “Amoniac”, nên dùng **Ammonia**, giữ “amoniac” ở cột Việt. |
| D36 | TT P264: “Giới thiệu”; mục kế tiếp “1.2.” | Thiếu số **1.1.** ở mục Giới thiệu nếu giữ hệ thống số mục. |
| D37 | TT P250; LA phần mô tả cấu trúc | “2 mục và 4 chương” dễ nhầm cấp section. Viết “Mở đầu, bốn chương và Kết luận/hướng phát triển”. “bốn bộ dữ liệu hỗn hợp khí” nên đổi “bốn bộ dữ liệu cảm biến khí”, vì drift gồm các phép đo khí riêng. |
| D38 | LA P1415: “hai loại hỗn hợp khí chính gồm ethylene–CO” | Câu nói hai nhưng liệt kê một. Nếu nghiên cứu chỉ dùng ethylene–CO, sửa “phần hỗn hợp ethylene–CO của bộ dữ liệu”; nếu giới thiệu toàn bộ nguồn, nêu thêm methane–ethylene rồi phân biệt phần được dùng. |
| D39 | LA P1427: “thời gian (tính bằng giây) ... tất cả ... ppm” | “tất cả” dễ bao gồm cột thời gian. Sửa “hai cột nồng độ có đơn vị ppm; cột thời gian có đơn vị giây”. |
| D40 | LA Bảng 3.2, P2466: “18,469” | Với Conv2D 3×3, 32 input channels, 64 filters và bias: (3×3×32+1)×64 = **18.496**. Có khả năng đảo hai chữ số. Kiểm tra kernel/use_bias của model trước khi sửa; các hàng lân cận đang phù hợp cấu hình này. |

## E Những điều không nên sửa nhầm

- Bảng 4.2 có 31,01 − 26,69 = 4,32 nhưng chênh lệch ghi 4,31; tương tự H₂/CO lệch 0,01 khi trừ các mean đã làm tròn. **V3 giữ các chênh lệch tính từ dữ liệu chưa làm tròn**. Không tự sửa 4,31 thành 4,32; nên thêm chú thích “chênh lệch tính từ số liệu chưa làm tròn”.
- 20 cảm biến, 378 lần phơi khí, 162.404 quan sát, 245 run CO và các MAE headline 13,9%/21,5%/27,5%/25,7% phù hợp V3. Lỗi chính nằm ở giao thức và diễn giải, không phải tự động thay các bảng này.
- Bảng drift cộng đúng **13.910** records; số liệu concentration ranges khớp nguồn UCI. Các vấn đề cần sửa là năm, nguồn trích và cách diễn giải tháng đo.
- Confusion matrix minh họa 174 TN + 6 FP + 12 FN + 116 TP = **308**, Accuracy = 290/308 ≈ **0,942**; báo cáo precision/recall/F1 làm tròn ở Bảng 3.8 phù hợp. Không sửa F1 0,94 chỉ vì bảng 5-fold là 0,91: cần ghi rõ protocol khác nhau.
- Hai ISSN khác nhau hoặc năm early access khác năm issue chưa đủ để kết luận một bên sai. Kiểm tra loại mã/năm trước khi đổi.
- OMML có các dấu mũ, dấu căn và delimiter không hiện trong plain-text extraction. Không đánh dấu “thiếu dấu mũ” chỉ vì bản trích chữ không hiện chúng. Các nhận xét công thức C13/C14 và A22 đã đối chiếu cấu trúc OMML.
- Word lưu một số hình/textbox dưới cả `mc:Choice` và `mc:Fallback`; đây không tự là hình/chú thích bị in hai lần.

## Nguồn đối chiếu và phạm vi xác minh

- [V3 Clean](../../Sensor_Aware_Transfer_Learning/V3.0/submission/IEEE_Revision_3.0_Clean.docx), đối chiếu văn bản đã có trong `proof/IEEE_Revision_3.0_Clean.txt`.
- [V3 Supplementary Evidence](../../Sensor_Aware_Transfer_Learning/V3.0/submission/SUPPLEMENTARY_EVIDENCE.docx), đặc biệt acquisition details, Physical timing, Tables S9–S10.
- [Xác nhận tác giả V3](../../Sensor_Aware_Transfer_Learning/V3.0/evidence/author_confirmations.md) và [lưu ý nguồn kế thừa](../../Sensor_Aware_Transfer_Learning/V3.0/evidence/SOURCE_NOTES.md). Không dùng metadata lịch sử v2.2 để phủ nhận xác nhận mới ở V3.
- V3 code: `code/same_device_session_transfer.py`, `code/revision_drift.py`, dùng kiểm tra learning rate và optimizer; không phải tái chạy thí nghiệm.
- [UCI drift](https://archive.ics.uci.edu/dataset/270/gas%2Bsensor%2Barray%2Bdrift%2Bdataset%2Bat%2Bdifferent%2Bconcentrations); [UCI dynamic mixtures](https://archive.ics.uci.edu/dataset/322/gas%2Bsensor%2Barray%2Bunder%2Bdynamic%2Bgas%2Bmixtures); [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html); [CatBoost](https://catboost.ai/docs/en/). Chỉ dùng thông tin trực tiếp cần thiết từ nguồn chính thức.
- Một số DOI bài báo không mở được qua công cụ web. Các nhận xét bibliographic tương ứng ghi **đối chiếu V3** hoặc **cần xác minh**, không được hiểu là đã xác thực toàn bộ danh mục với publisher.

Khi sửa, nên xử lý A01–A13 trước, rồi đồng bộ Chương 2, Chương 4, mở đầu/kết luận và TT; sau đó cập nhật cross-reference/caption, rà chính tả và render Word để kiểm tra bố cục toàn bộ trang.
