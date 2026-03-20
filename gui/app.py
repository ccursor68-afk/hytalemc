"""CustomTkinter tabanli ana uygulama penceresi."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from converter.mapper import BlockMapper
from converter.reader import read_schematic
from converter.writer import write_prefab
from gui.components import QueueItemWidget

SUPPORTED_EXTENSIONS = {".schematic", ".schem", ".litematic"}


@dataclass(slots=True)
class QueueItem:
    """Donusturme kuyrugundaki dosya kaydini tutar."""

    path: Path
    status: str = "waiting"
    error: str = ""


class HytaleConverterApp:
    """Minecraft -> Hytale toplu donusum GUI uygulamasi."""

    def __init__(self) -> None:
        """Ana pencereyi, durum degiskenlerini ve servisleri hazirlar."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Minecraft -> Hytale Schematic Converter")
        self.root.geometry("1200x760")
        self.root.minsize(1080, 680)

        self.mapper = BlockMapper()

        self.queue_items: list[QueueItem] = []
        self.item_widgets: dict[Path, QueueItemWidget] = {}
        self.selected_path: Path | None = None
        self.last_report: str = ""

        self.same_folder_var = ctk.BooleanVar(value=False)
        self.strict_mode_var = ctk.BooleanVar(value=False)
        self.output_dir_var = ctk.StringVar(value=str(Path.cwd() / "output"))

        self._event_queue: queue.Queue[tuple] = queue.Queue()
        self._worker_thread: threading.Thread | None = None
        self._build_layout()
        self._poll_events()

    def _build_layout(self) -> None:
        """Sol kuyruk paneli ve sag kontrol paneli arayuzunu kurar."""
        container = ctk.CTkFrame(self.root)
        container.pack(fill="both", expand=True, padx=12, pady=12)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        left_panel = ctk.CTkFrame(container)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(1, weight=1)

        left_top = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        left_top.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(left_top, text="Dosya Ekle", command=self.add_files).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ctk.CTkButton(left_top, text="Klasor Ekle", command=self.add_folder).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        self.queue_frame = ctk.CTkScrollableFrame(left_panel, label_text="Donusum Kuyrugu")
        self.queue_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        self.queue_frame.grid_columnconfigure(0, weight=1)

        left_bottom = ctk.CTkFrame(left_panel, fg_color="transparent")
        left_bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(8, 12))
        left_bottom.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(left_bottom, text="Secileni Kaldir", command=self.remove_selected).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ctk.CTkButton(left_bottom, text="Tumunu Temizle", command=self.clear_all).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        right_panel = ctk.CTkFrame(container)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(4, weight=1)

        self._build_settings(right_panel)

        self.convert_button = ctk.CTkButton(
            right_panel,
            text="DONUSTUR",
            fg_color="#2E8B57",
            hover_color="#247048",
            height=56,
            font=ctk.CTkFont(size=20, weight="bold"),
            command=self.start_conversion,
        )
        self.convert_button.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 8))

        self.overall_progress = ctk.CTkProgressBar(right_panel)
        self.overall_progress.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.overall_progress.set(0)

        self.summary_label = ctk.CTkLabel(right_panel, text="Hazir")
        self.summary_label.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 8))

        self.log_box = ctk.CTkTextbox(right_panel, wrap="word")
        self.log_box.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 10))
        self.log_box.configure(state="disabled")

        ctk.CTkButton(right_panel, text="Raporu Kaydet", command=self.save_report).grid(
            row=5, column=0, sticky="ew", padx=12, pady=(0, 12)
        )

    def _build_settings(self, parent) -> None:
        """Sag paneldeki ayarlar bolumunu olusturur."""
        settings = ctk.CTkFrame(parent)
        settings.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        settings.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(settings, text="Ayarlar", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=(8, 6)
        )

        output_row = ctk.CTkFrame(settings, fg_color="transparent")
        output_row.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        output_row.grid_columnconfigure(0, weight=1)
        self.output_entry = ctk.CTkEntry(output_row, textvariable=self.output_dir_var)
        self.output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(output_row, text="Sec", width=70, command=self.pick_output_folder).grid(
            row=0, column=1, sticky="e"
        )

        ctk.CTkCheckBox(
            settings,
            text="Ciktiyi kaynak dosyayla ayni klasore koy",
            variable=self.same_folder_var,
        ).grid(row=2, column=0, sticky="w", padx=8, pady=4)

        ctk.CTkCheckBox(
            settings,
            text="Eslesmeyen bloklarda hata ver (strict)",
            variable=self.strict_mode_var,
        ).grid(row=3, column=0, sticky="w", padx=8, pady=(4, 8))

    def run(self) -> None:
        """Tkinter event dongusunu baslatir."""
        self.root.mainloop()

    def add_files(self) -> None:
        """Kullanicidan birden cok dosya secip kuyruga ekler."""
        filetypes = [("Schematic Files", "*.schem *.schematic *.litematic")]
        selected = filedialog.askopenfilenames(title="Dosya Sec", filetypes=filetypes)
        for p in selected:
            self._try_add_path(Path(p))

    def add_folder(self) -> None:
        """Secilen klasor altindaki uygun dosyalari kuyruga ekler."""
        folder = filedialog.askdirectory(title="Klasor Sec")
        if not folder:
            return
        base = Path(folder)
        found = 0
        for ext in SUPPORTED_EXTENSIONS:
            for file_path in base.rglob(f"*{ext}"):
                self._try_add_path(file_path)
                found += 1
        self._log(f"Klasorden toplam {found} dosya tarandi.")

    def _try_add_path(self, file_path: Path) -> None:
        """Desteklenen ve tekrar etmeyen dosyalari kuyruga ekler."""
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            self._log(f"Desteklenmeyen format atlandi: {file_path.name}")
            return
        if any(item.path == file_path for item in self.queue_items):
            return

        item = QueueItem(path=file_path)
        self.queue_items.append(item)
        self._create_item_widget(item)
        self._log(f"Kuyruga eklendi: {file_path.name}")

    def _create_item_widget(self, item: QueueItem) -> None:
        """Queue item icin satir widget olusturup listeye yerlestirir."""
        widget = QueueItemWidget(
            self.queue_frame,
            file_name=item.path.name,
            on_select=lambda w: self._select_widget(item.path, w),
        )
        widget.grid(row=len(self.item_widgets), column=0, sticky="ew", padx=4, pady=4)
        self.item_widgets[item.path] = widget

    def _select_widget(self, path: Path, selected_widget: QueueItemWidget) -> None:
        """Kullanici secimini takip eder ve satir vurgusunu gunceller."""
        self.selected_path = path
        for p, widget in self.item_widgets.items():
            widget.set_selected(widget is selected_widget and p == path)

    def remove_selected(self) -> None:
        """Secilen dosyayi kuyruktan kaldirir."""
        if not self.selected_path:
            return
        self.queue_items = [item for item in self.queue_items if item.path != self.selected_path]
        self.selected_path = None
        self._rebuild_queue_ui()
        self._log("Secili dosya kuyruktan kaldirildi.")

    def clear_all(self) -> None:
        """Tum dosya kuyrugunu sifirlar."""
        self.queue_items.clear()
        self.selected_path = None
        self._rebuild_queue_ui()
        self.overall_progress.set(0)
        self.summary_label.configure(text="Hazir")
        self._log("Tum kuyruk temizlendi.")

    def _rebuild_queue_ui(self) -> None:
        """Queue satirlarini temizleyip mevcut item'lara gore yeniden cizer."""
        for widget in self.item_widgets.values():
            widget.destroy()
        self.item_widgets.clear()
        for item in self.queue_items:
            self._create_item_widget(item)

    def pick_output_folder(self) -> None:
        """Cikti klasoru secimini dosya secici ile yapar."""
        folder = filedialog.askdirectory(title="Cikti Klasoru Sec")
        if folder:
            self.output_dir_var.set(folder)
            self._log(f"Cikti klasoru secildi: {folder}")

    def start_conversion(self) -> None:
        """Thread uzerinde donusum surecini baslatir."""
        if self._worker_thread and self._worker_thread.is_alive():
            messagebox.showinfo("Bilgi", "Donusum zaten devam ediyor.")
            return
        if not self.queue_items:
            messagebox.showwarning("Uyari", "Lutfen once dosya ekleyin.")
            return

        # Yazma izni kontrolu: kaynak klasore yaz secili degilse output klasor test edilir.
        if not self.same_folder_var.get():
            output_dir = Path(self.output_dir_var.get().strip())
            if not self._check_output_writable(output_dir):
                msg = "Cikti klasoru yazilabilir degil."
                self._log(msg)
                messagebox.showerror("Hata", msg)
                return

        self.convert_button.configure(state="disabled")
        self.overall_progress.set(0)
        self.summary_label.configure(text="Donusum basladi...")

        for item in self.queue_items:
            item.status = "waiting"
            item.error = ""
            if item.path in self.item_widgets:
                self.item_widgets[item.path].set_status("⏳")
                self.item_widgets[item.path].set_progress(0)

        self._worker_thread = threading.Thread(target=self._convert_worker, daemon=True)
        self._worker_thread.start()

    def _check_output_writable(self, folder: Path) -> bool:
        """Cikti klasorune yazma izni olup olmadigini test eder."""
        try:
            folder.mkdir(parents=True, exist_ok=True)
            probe = folder / ".write_test.tmp"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def _convert_worker(self) -> None:
        """Arka planda dosyalari sirayla donusturup event queue'ya durum yazar."""
        total = len(self.queue_items)
        success = 0
        failed = 0
        errors: list[str] = []

        for index, item in enumerate(self.queue_items, start=1):
            self._event_queue.put(("file_start", item.path))
            try:
                blocks = read_schematic(item.path)
                self._event_queue.put(("file_progress", item.path, 0.4))
                mapped_blocks = self.mapper.map_blocks(blocks)
                self._event_queue.put(("file_progress", item.path, 0.8))

                if self.same_folder_var.get():
                    output_dir = item.path.parent
                else:
                    output_dir = Path(self.output_dir_var.get().strip())
                output_file = output_dir / f"{item.path.stem}.prefab.json"

                write_prefab(blocks=mapped_blocks, output_path=output_file)
                success += 1
                self._event_queue.put(("file_done", item.path, True, ""))
            except (ValueError, PermissionError, OSError) as exc:
                failed += 1
                error = str(exc)
                errors.append(f"{item.path.name}: {error}")
                self._event_queue.put(("file_done", item.path, False, error))
            except Exception as exc:
                failed += 1
                error = f"Beklenmeyen hata: {exc}"
                errors.append(f"{item.path.name}: {error}")
                self._event_queue.put(("file_done", item.path, False, error))

            self._event_queue.put(("overall_progress", index / total))

        report_lines = [
            "Donusum Raporu",
            "=" * 40,
            f"Toplam dosya: {total}",
            f"Basarili: {success}",
            f"Hatali: {failed}",
            "",
        ]
        if errors:
            report_lines.append("Hata Listesi:")
            report_lines.extend(f"- {line}" for line in errors)
        else:
            report_lines.append("Tum dosyalar basariyla donusturuldu.")
        self.last_report = "\n".join(report_lines)
        self._event_queue.put(("finished", success, failed))

    def _poll_events(self) -> None:
        """Worker thread event'lerini alip GUI uzerinde gunceller."""
        try:
            while True:
                event = self._event_queue.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _handle_event(self, event: tuple) -> None:
        """Event tipine gore satir ve genel durum bilgisini yeniler."""
        etype = event[0]
        if etype == "file_start":
            path = event[1]
            self._log(f"Donusum basladi: {Path(path).name}")
            if path in self.item_widgets:
                self.item_widgets[path].set_status("⏳")
                self.item_widgets[path].set_progress(0.1)
        elif etype == "file_progress":
            path, value = event[1], event[2]
            if path in self.item_widgets:
                self.item_widgets[path].set_progress(float(value))
        elif etype == "file_done":
            path, ok, error = event[1], event[2], event[3]
            for item in self.queue_items:
                if item.path == path:
                    item.status = "done" if ok else "error"
                    item.error = error
                    break
            if path in self.item_widgets:
                self.item_widgets[path].set_progress(1.0)
                self.item_widgets[path].set_status("✅" if ok else "❌")
            if ok:
                self._log(f"Basarili: {Path(path).name}")
            else:
                self._log(f"Hata: {Path(path).name} -> {error}")
        elif etype == "overall_progress":
            self.overall_progress.set(float(event[1]))
        elif etype == "finished":
            success, failed = event[1], event[2]
            self.convert_button.configure(state="normal")
            self.summary_label.configure(
                text=f"Donusum bitti | Basarili: {success} | Hatali: {failed}"
            )
            self._log("Toplu donusum tamamlandi.")

    def _log(self, message: str) -> None:
        """Log alanina zaman damgasi ile yeni satir ekler."""
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"
        self.log_box.configure(state="normal")
        self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def save_report(self) -> None:
        """Son olusturulan raporu .txt dosyasina kaydeder."""
        if not self.last_report:
            messagebox.showinfo("Bilgi", "Henuz kaydedilecek rapor yok.")
            return
        target = filedialog.asksaveasfilename(
            title="Raporu Kaydet",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
        )
        if not target:
            return
        try:
            Path(target).write_text(self.last_report, encoding="utf-8")
            self._log(f"Rapor kaydedildi: {target}")
        except Exception as exc:
            err = f"Rapor kaydedilemedi: {exc}"
            self._log(err)
            messagebox.showerror("Hata", err)
