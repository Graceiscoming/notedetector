### 👤 1. User Requirements (สิ่งที่ User ต้องการจากโปรแกรมนี้)

User ที่ใช้งานโปรแกรมนี้ (ซึ่งก็คือเกรซ) มีเป้าหมายหลักคือการแปลงเสียงเพลงให้เป็นโน้ตดนตรีที่แม่นยำที่สุด โดยระบบต้องตอบสนองความต้องการดังนี้:

1. **รองรับไฟล์เพลงเต็มรูปแบบ:** สามารถอัปโหลดไฟล์เพลง (เช่น `.wav`, `.mp3`) ที่มีเครื่องดนตรีหลายชิ้นเล่นพร้อมกันได้
2. **เลือกแยกชิ้นดนตรีได้:** ต้องการเลือกได้ว่าจะสกัดเสียงอะไรออกมาเป็นเมโลดี้หลัก เช่น เลือกสกัดเฉพาะ "เสียงร้อง", "เสียงเปียโน" หรือ "เสียงกีตาร์" โดยไม่มีเสียงดนตรีอื่นรบกวน
3. **ระบบวิเคราะห์ Key เพลง:** ต้องการให้โปรแกรมบอกได้ว่าเพลงที่อัปโหลดน่าจะอยู่ใน Key อะไร (เช่น C Major, A Minor)
4. **กำหนด Key เองได้ (Manual Override):** หากรู้ Key ของเพลงอยู่แล้ว ต้องการฟังก์ชันสำหรับพิมพ์ระบุ Key เข้าไปเอง เพื่อบังคับให้โปรแกรมใช้ Key นั้นในการคำนวณ
5. **ความแม่นยำระดับสูงสุด ไร้โน้ตขยะ:** ต้องการให้ระบบตัด "โน้ตขยะ" (Garbage Notes) หรืออาการเสียงแกว่งทิ้งไป โดยโน้ตที่ออกมาต้องตรงตามสเกลของ Key ที่ตั้งไว้เท่านั้น (Smart Pitch Snapping)
6. **นำไปใช้งานต่อได้ทันที:** ต้องการผลลัพธ์สุดท้ายเป็นไฟล์ `.mid` (MIDI) ที่สามารถลากไปวางในโปรแกรมทำเพลง (DAW) แล้วเล่นโน้ตได้เป๊ะๆ ทันที

---

### ⚙️ 2. Functional Requirements (ฟังก์ชันการทำงานที่ต้องมีในระบบ)

เพื่อให้บรรลุ User Requirements ด้านบน โปรแกรมจะต้องมีระบบการทำงานย่อย (Modules) ที่ห้ามขาดหายไปดังต่อไปนี้:

* **F1: Audio Ingestion Module (ระบบจัดการไฟล์เสียงรับเข้า)**
  * รับไฟล์ Audio เข้ามาและแปลงให้อยู่ในรูปแบบ Mono (Channel เดียว) และปรับ Sample Rate ให้เหมาะสมกับ AI Model (เช่น 44100 Hz)
  * ✅ **[ปรับปรุง]** ใช้ `soundfile` สำหรับโหลดไฟล์ขนาดใหญ่ (เร็วกว่า `librosa.load` 3-5x) และใช้ `torchaudio.transforms.Resample` บน GPU สำหรับ Resampling (เร็วกว่า CPU 2-4x)


* **F2: Advanced Source Separation Module (ระบบสกัดและแยกชิ้นเครื่องดนตรี)**
  * ใช้ AI ถอดรหัสไฟล์เพลงเต็ม (Polyphonic) เพื่อสร้างไฟล์เสียงชั่วคราวที่เป็น "เสียงเดี่ยว" (Isolated Track) ตามที่ผู้ใช้เลือก (เช่น สกัดเฉพาะ Vocal หรือเฉพาะ Piano)
  * ✅ **[ปรับปรุง]** เลือกโมเดลตามงาน:
    * **Vocal:** ใช้ **BS-RoFormer** (แม่นที่สุดสำหรับเสียงร้อง) — แต่ต้อง Unload ทันทีหลังใช้เพราะกินหน่วยความจำ ~5-6GB
    * **ดนตรี/เครื่องดนตรีทั่วไป:** ใช้ **MDX23C** หรือ **Demucs v4 (htdemucs_ft)** แทน — เบากว่าและสมดุลกว่าสำหรับ VRAM 8GB


* **F3: Key Detection & Override Module (ระบบวิเคราะห์และรับค่า Key)**
  * **Auto-Detect:** ✅ **[ปรับปรุง]** ใช้ **Voting Ensemble 3 วิธี** แล้ว Vote เลือกผลที่ตรงกันมากที่สุด (เพิ่มความแม่นจาก ~70% → ~90%)
    1. **Krumhansl-Schmuckler** (librosa Chromagram Template Matching)
    2. **Temperley Profile** (อีก Template ต่างสไตล์)
    3. **Simple Chroma Energy** (โน้ตที่มี Energy สูงสุดในแต่ละ Octave)
  * **Manual Input:** มีตัวแปร (Variable) หรือช่องทางรับค่าจากผู้ใช้ให้บังคับระบุ Key (เช่น `target_key = "G_Major"`) ซึ่งจะ Bypass การ Auto-Detect ทั้งหมด
  * ตั้งค่าทั้งหมดผ่าน `config.yaml` (ดูหัวข้อ 4)


* **F4: Dual-Engine Pitch Tracking Module (ระบบแกะโน้ตความละเอียดสูง)**
  * **Mode A (Monophonic):** สำหรับเสียงร้องหรือเครื่องเป่า ใช้ **`torchcrepe`** (model=`'full'`) รันบน GPU ทำ Frame-level F₀ analysis — แม่นที่สุดสำหรับ Vocal
    * ✅ **[ปรับปรุง]** ตั้ง `batch_size=512` เพื่อ Maximize GPU Throughput (เร็วขึ้น 30-50%)
  * **Mode B (Polyphonic):** ✅ **[ปรับปรุง]** เปลี่ยนจาก `basic-pitch` → **`piano_transcription_inference`** (แม่นกว่ามากสำหรับ Piano และ Chord, มี GPU Support) รวมถึงน้ำหนักการกด (Velocity)


* **F5: Intelligent Pitch Snapping & Filtering Module (ระบบกรองโน้ตด้วยทฤษฎีดนตรี)** *<- ฟังก์ชันสำคัญที่เกรซรีเควส*
  * รับข้อมูล Key จาก F3 มาสร้างเป็น "ตารางโน้ตที่อนุญาตให้มีได้" (Allowed Notes Array)
  * นำค่าความถี่ (Hz) จาก F4 มาแปลงเป็นโน้ต แล้วเทียบกับตารางโน้ต
  * **Note Segmentation:** ทำการจัดกลุ่มความถี่ทีละเฟรม ร่วมกับข้อมูลความดัง (Amplitude/Energy Onset) เพื่อระบุจุดเริ่มและจุดจบของโน้ตแต่ละตัว
  * ✅ **[ปรับปรุง — Pre-processing]** ใช้ **Median Filter** บน Pitch Sequence ก่อน Segment เพื่อกรองค่า Pitch ที่กระโดดผิดปกติออก (ป้องกันโน้ตสั้นกระจัดกระจาย)
  * ✅ **[ปรับปรุง — Minimum Duration]** ปรับ Threshold เป็น **≥ 0.08s** (จากเดิม 0.05s) เพื่อกรองเสียงรบกวนที่เป็นโน้ตสั้นผิดปกติออกให้ดียิ่งขึ้น
  * ✅ **[ปรับปรุง — Note Merging]** รวมโน้ต Pitch เดียวกันที่มี Gap ระหว่างกันน้อยกว่า **0.05s** ให้กลายเป็นโน้ตตัวเดียว (ป้องกันโน้ตตัวเดียวถูกตัดเป็นหลายตัว)
  * ✅ **[ปรับปรุง — Smarter Snapping]** เปลี่ยน Logic การ Snap:
    * ถ้า Pitch ห่างจากโน้ตใน Key **≤ 50 cents** → Snap เข้าหาโน้ตที่ใกล้ที่สุดตามปกติ
    * ถ้า Pitch ห่างจากโน้ตใน Key **> 50 cents** → **ลบโน้ตนั้นทิ้งเลย** (เป็นเสียงรบกวนที่ Snap แล้วจะได้โน้ตที่ไม่มีความหมายทางดนตรี)
  * **VRAM Clean up:** ทำความสะอาดหน่วยความจำ GPU (`torch.cuda.empty_cache()`) ทุกครั้งหลังสลับกระบวนการทำงานเพื่อเลี่ยง VRAM เต็ม (เนื่องจากมี VRAM 8GB)


* **F6: MIDI Generation Module (ระบบสร้างไฟล์ MIDI)**
  * นำข้อมูล ตัวโน้ต (Pitch), เวลาเริ่ม (Onset), เวลาจบ (Offset) และ น้ำหนักเสียง (Velocity) มาประกอบร่างและ Export เป็นไฟล์ `.mid`


---

### 📚 3. System Requirements & Library Stack

เพื่อให้สอดคล้องกับฮาร์ดแวร์ CPU i7-8700k, RAM 32GB และ **GPU GTX 1070 Ti (VRAM 8GB)** นี่คือเทคโนโลยีที่ต้องใช้ทั้งหมด:

**Core Environment:**

* **Python:** เวอร์ชัน 3.10 หรือ 3.11 (แนะนำ 3.10.12 จะเสถียรสุดกับ AI Audio)
* **CUDA Toolkit:** เวอร์ชัน 11.8 หรือ 12.1 (สำหรับให้ AI เรียกใช้การ์ดจอ)

**Libraries ที่บังคับใช้ (The Tech Stack):**

1. `torch`, `torchaudio`, `torchvision`: Framework หลักในการรัน AI ต้องลงเวอร์ชันที่ลงท้ายด้วย `+cu118` หรือ `+cu121`
2. `audio-separator`: สำหรับ F2 (Source Separation) เรียกใช้โมเดล **BS-RoFormer** (แยกเสียงร้อง) หรือ **MDX23C / Demucs v4 htdemucs_ft** (แยกดนตรีทั่วไป)
3. `soundfile`: สำหรับ F1 โหลดไฟล์ Audio ขนาดใหญ่เร็วกว่า librosa 3-5x ✅ **[เพิ่มใหม่]**
4. `librosa` + `numpy`: สำหรับ F3 (Key Detection) คำนวณ Chromagram และใช้ Template Matching (Krumhansl-Schmuckler + Temperley) ใน Voting Ensemble (หลีกเลี่ยง `essentia-tensorflow` เพื่อหลีกเลี่ยงปัญหาติดตั้งยากและแครชบน Windows)
5. `torchcrepe`: สำหรับ F4 Mode A (Monophonic) โมเดลจับความถี่เสียงร้องระดับเสี้ยววินาที รันบน GPU ด้วย `batch_size=512`
6. ✅ **[ปรับปรุง]** `piano_transcription_inference`: สำหรับ F4 Mode B (Polyphonic) แกะโน้ตเปียโน/เครื่องดนตรีหลายชิ้น — แม่นกว่า `basic-pitch` มาก (แทนที่ `basic-pitch`)
7. `librosa`: สำหรับประมวลผลสัญญาณเสียงพื้นฐาน ดึงค่า Array แปลงความถี่ Hz เป็น MIDI Number และทำ Onset Detection
8. `pretty_midi`: สำหรับ F6 ใช้เขียนโค้ดเพื่อ Generate ไฟล์ `.mid`
9. `numpy`, `scipy`: สำหรับ F5 จัดการคณิตศาสตร์ อาเรย์ Median Filter และการคำนวณปัดเศษตัวโน้ต (Pitch Snapping)
10. `pyyaml`: สำหรับอ่านไฟล์ `config.yaml` ✅ **[เพิ่มใหม่]**

**VRAM Management Strategy (สำคัญมากสำหรับ 8GB):**
* โหลดโมเดล AI **ทีละตัว** (Sequential) — รัน → Unload → `del model` → `torch.cuda.empty_cache()` → `gc.collect()` ก่อนโหลดตัวถัดไป
* ตั้ง `torch.cuda.set_per_process_memory_fraction(0.85)` เพื่อป้องกัน OOM Crash
* **ห้ามโหลดโมเดล 2 ตัวขึ้นไปพร้อมกันบน GPU**

---

### 📂 4. Project Structure (โครงสร้างไดเรกทอรีโปรเจกต์)

การวางโครงสร้างแบบนี้จะทำให้เกรซจัดการโค้ดได้ง่าย ไม่สับสนเวลาโมเดล AI โหลดไฟล์ครับ:

```text
notedee/
│
├── config.yaml             # ✅ [เพิ่มใหม่] รวม Parameters ทั้งหมด (key, thresholds, model paths, batch_size)
├── input_audio/            # โฟลเดอร์สำหรับนำไฟล์ mp3/wav ที่ต้องการแกะมาวาง
├── output_midi/            # โฟลเดอร์เก็บไฟล์ .mid ที่โปรแกรมประมวลผลเสร็จแล้ว
├── temp_separated/         # โฟลเดอร์พักไฟล์เสียงที่ถูกแยกชิ้นดนตรีแล้ว (RoFormer จะพ่นไฟล์มาไว้ที่นี่)
├── models/                 # (Optional) โฟลเดอร์เก็บไฟล์ Weights ของ AI รุ่นต่างๆ หากโหลดแบบ Offline
│
├── requirements.txt        # ไฟล์ระบุชื่อ Library และเวอร์ชันที่ต้องใช้ (ใช้รัน pip install -r)
├── main.py                 # ไฟล์รันโปรแกรมหลัก เป็นตัวควบคุม Pipeline ทั้งหมด
│
└── src/                    # โฟลเดอร์เก็บ Source Code แยกตามฟังก์ชันการทำงาน
    ├── __init__.py
    ├── audio_ingest.py       # ✅ [เปลี่ยนชื่อ] F1: โหลดและ Resample Audio ด้วย soundfile + torchaudio
    ├── source_separator.py   # ✅ [เปลี่ยนชื่อ] F2: เรียก BS-RoFormer/MDX23C (เดิม audio_separator.py — ชื่อชนกับ library!)
    ├── key_detector.py       # F3: Voting Ensemble Key Detection (KS + Temperley + Chroma Energy)
    ├── pitch_tracker.py      # F4: เรียก torchcrepe (Mono) หรือ piano_transcription_inference (Poly)
    ├── pitch_filter.py       # F5: Median Filter → Segment → Merge → Smart Snap → Min Duration Filter
    ├── midi_exporter.py      # F6: รับ Array มาแปลงเป็นไฟล์ .mid ด้วย pretty_midi
    └── utils/                # ✅ [เพิ่มใหม่] โฟลเดอร์ Helper Functions
        ├── memory_manager.py  # Centralize VRAM cleanup (del + empty_cache + gc.collect)
        └── audio_utils.py     # ฟังก์ชัน Helper ทั่วไปด้าน Audio
```

> **หมายเหตุสำคัญ:** ชื่อไฟล์ `audio_separator.py` จะ **ชนชื่อกับ library `audio-separator`** ที่ติดตั้งไว้ทำให้ Import Error — เปลี่ยนเป็น `source_separator.py` เสมอ


 ลำดับการพัฒนา (Phases)
Phase 1: Environment Setup & Audio Ingestion (วางรากฐานการรับไฟล์)
เป้าหมาย: โปรแกรมสามารถรับไฟล์เสียงเข้ามา แปลงฟอร์แมต และพร้อมส่งต่อให้ AI ได้

ติดตั้ง Libraries: ทดสอบการติดตั้ง requirements.txt ให้มั่นใจว่า PyTorch ใช้งาน GPU (CUDA) ได้จริง
[F1] Audio Ingestion (audio_ingest.py): เขียนฟังก์ชันโหลดไฟล์ด้วย soundfile และทำ Resampling ด้วย torchaudio.transforms.Resample บน GPU
การทดสอบ: ลองรันโหลดไฟล์ .mp3/.wav จริงๆ เพื่อดูว่าโปรแกรมโหลดได้เร็วและไม่มี Error
Phase 2: Source Separation & VRAM Management (ระบบสกัดเสียงและคุมหน่วยความจำ)
เป้าหมาย: สามารถสกัดเสียงร้องหรือเสียงเปียโนออกมาเป็นไฟล์เสียงเดี่ยวได้ โดยที่การ์ดจอไม่แครช

[Utils] Memory Manager (memory_manager.py): เขียนระบบเคลียร์ VRAM (del, empty_cache, gc.collect) ให้พร้อมใช้งาน
[F2] Source Separator (source_separator.py): นำ audio-separator มาเชื่อมต่อ รองรับโมเดล BS-RoFormer และ MDX23C/htdemucs
การทดสอบ: ดึงเสียงจาก Phase 1 มาสกัดเป็นเสียงร้องล้วนๆ และตรวจสอบ VRAM usage ว่าอยู่ในเกณฑ์ 8GB
Phase 3: Key Detection (ระบบวิเคราะห์สเกลเพลง)
เป้าหมาย: โปรแกรมสามารถวิเคราะห์ได้ว่าเพลงนั้นอยู่ใน Key อะไร เพื่อนำไปใช้กรองโน้ตในภายหลัง

[F3] Key Detector (key_detector.py): สร้างระบบ Voting Ensemble (Krumhansl-Schmuckler, Temperley, Chroma Energy) โดยใช้ librosa
ระบบ Manual Override: ดึงค่า Override จาก config.yaml หากผู้ใช้ระบุ Key มาเอง
การทดสอบ: นำไฟล์เพลงที่รู้ Key อยู่แล้วมาทดสอบความแม่นยำของระบบ Auto-Detect
Phase 4: Pitch Tracking & Basic MIDI (แกะโน้ตและสร้าง MIDI เบื้องต้น)
เป้าหมาย: ใช้ AI แกะโน้ตจากเสียงที่แยกมาแล้ว และเซฟเป็นไฟล์ .mid ได้

[F4] Pitch Tracker (pitch_tracker.py):
เชื่อมต่อ torchcrepe สำหรับเสียงร้อง (Monophonic)
เชื่อมต่อ piano_transcription_inference สำหรับชิ้นดนตรี (Polyphonic)
[F6] MIDI Exporter (midi_exporter.py): นำค่า Pitch/Onset/Offset มาสร้างไฟล์ .mid ด้วย pretty_midi
การทดสอบ: สร้างไฟล์ MIDI ดิบ (ยังไม่กรองโน้ตขยะ) เพื่อดูว่า AI แกะความถี่ออกมาได้ตรงกับเสียงจริงไหม
Phase 5: Intelligent Pitch Snapping & Filtering (ระบบเวทมนตร์กรองโน้ตขยะ) 🌟 จุดสำคัญ
เป้าหมาย: ทำให้ไฟล์ MIDI สะอาด เป๊ะตามสเกล ไม่มีโน้ตสั้นๆ หรือโน้ตขยะกวนใจ

[F5] Pitch Filter (pitch_filter.py):
นำ Key จาก Phase 3 มาสร้างตารางตีกรอบ (Allowed Notes)
ทำ Median Filter กรองความถี่ที่แกว่ง
จัดการแบ่งและเชื่อมโน้ต (Min Duration 0.08s, Merge Gap 0.05s)
Smart Snap (ถ้าระยะห่าง <= 50 cents ให้ดึงเข้าสเกล, ถ้า > 50 cents ให้ลบทิ้ง)
การทดสอบ: นำเสียงร้องมาแกะ และเปรียบเทียบไฟล์ MIDI ระหว่าง "ก่อนกรอง" (Phase 4) และ "หลังกรอง" (Phase 5)
Phase 6: E2E Pipeline Integration & Polish (ประกอบร่างและขัดเกลา)
เป้าหมาย: รวมทุกอย่างเข้าด้วยกันที่ main.py และปรับจูนความแม่นยำ

Main Pipeline (main.py): ประกอบ F1 -> F2 -> F3 -> F4 -> F5 -> F6 ให้รันต่อเนื่องในคลิกเดียว
การทดสอบจริง: โยนไฟล์เพลงเต็มเข้ามา 1 เพลง แล้วรอรับไฟล์ MIDI ที่ใช้งานได้จริงตอนจบ
Fine-Tuning: ปรับแก้ค่า Thresholds ใน config.yaml จากผลลัพธ์การทดลองจริง