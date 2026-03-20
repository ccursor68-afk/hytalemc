"""
Hytale Converter - Modern Dark UI
CustomTkinter + ttk ile profesyonel arayuz
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime
import threading
import queue
import sys
import os

# Converter modulleri
from converter.reader import read_schematic
from converter.mapper import BlockMapper
from converter.writer import write_prefab


def resource_path(relative_path: str) -> str:
    """PyInstaller icin kaynak dosya yolu"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# =============================================================================
# RENK PALETI
# =============================================================================
COLORS = {
    "bg_darkest":   "#080c12",
    "bg_dark":      "#0a0e14",
    "bg_main":      "#0d1117",
    "bg_panel":     "#0d2040",
    "border":       "#1e3a5f",
    "border_hover": "#2a5a90",
    "accent":       "#0066cc",
    "accent_light": "#66aaff",
    "text_primary": "#a0c0e0",
    "text_muted":   "#4a6a8a",
    "text_mono":    "#7aa8d4",
    "success":      "#00cc88",
    "warning":      "#aaaa00",
    "error":        "#ff4444",
    "btn_convert":  "#002a60",
    "btn_convert_hover": "#003a80",
    "btn_convert_border": "#0055cc",
}

# Font ayarlari
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)
FONT_HEADER = ("Segoe UI", 11, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_BUTTON = ("Segoe UI", 9, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")

VERSION = "2.0.0"


# =============================================================================
# DOSYA DURUMU
# =============================================================================
class FileStatus:
    PENDING = "BEKLE"
    PROCESSING = "ISLEM"
    SUCCESS = "TAMAM"
    ERROR = "HATA"


# =============================================================================
# ANA UYGULAMA
# =============================================================================
class HytaleConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Pencere ayarlari
        self.title("HYTALE CONVERTER")
        self.geometry("920x580")
        self.minsize(800, 500)
        
        # Tema
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLORS["bg_main"])
        
        # Ikon
        try:
            icon_path = resource_path("assets/icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass
        
        # Degiskenler
        self.files_queue = []  # [(path, status, progress), ...]
        self.output_dir = Path.home() / "Documents" / "HytaleConverter"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.is_converting = False
        self.log_queue = queue.Queue()
        
        # Sayaclar
        self.success_count = 0
        self.error_count = 0
        
        # UI olustur
        self._create_ui()
        
        # Log queue'u kontrol et
        self._check_log_queue()
    
    def _create_ui(self):
        """Ana UI'i olustur"""
        # Ust baslik bari
        self._create_title_bar()
        
        # Ana icerik (sol ve sag panel)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=0)  # ayirici
        self.content_frame.grid_columnconfigure(2, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Sol panel - Dosya kuyrugu
        self._create_left_panel()
        
        # Dikey ayirici
        separator = ctk.CTkFrame(
            self.content_frame,
            width=1,
            fg_color=COLORS["border"]
        )
        separator.grid(row=0, column=1, sticky="ns", padx=8)
        
        # Sag panel - Kontrol
        self._create_right_panel()
    
    def _create_title_bar(self):
        """Ust baslik bari"""
        title_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_dark"],
            height=50,
            corner_radius=0
        )
        title_frame.pack(fill="x", padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        # Sol taraf - ikon ve baslik
        left_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        left_frame.pack(side="left", padx=16, pady=8)
        
        # Altigen ikon (unicode)
        icon_label = ctk.CTkLabel(
            left_frame,
            text="⬡",
            font=("Segoe UI", 24),
            text_color=COLORS["accent"]
        )
        icon_label.pack(side="left", padx=(0, 8))
        
        # Baslik
        title_label = ctk.CTkLabel(
            left_frame,
            text="H Y T A L E   C O N V E R T E R",
            font=FONT_TITLE,
            text_color=COLORS["text_primary"]
        )
        title_label.pack(side="left")
        
        # PRO badge
        pro_badge = ctk.CTkLabel(
            left_frame,
            text=" PRO ",
            font=("Segoe UI", 8, "bold"),
            fg_color=COLORS["accent"],
            text_color="white",
            corner_radius=4,
            padx=6,
            pady=2
        )
        pro_badge.pack(side="left", padx=(12, 0))
        
        # Sag taraf - versiyon
        version_label = ctk.CTkLabel(
            title_frame,
            text=f"v{VERSION}",
            font=FONT_MONO_SMALL,
            text_color=COLORS["text_muted"]
        )
        version_label.pack(side="right", padx=16)
    
    def _create_left_panel(self):
        """Sol panel - Dosya kuyrugu"""
        left_panel = ctk.CTkFrame(
            self.content_frame,
            fg_color=COLORS["bg_dark"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=6
        )
        left_panel.grid(row=0, column=0, sticky="nsew")
        
        # Header
        header = ctk.CTkFrame(left_panel, fg_color="transparent", height=44)
        header.pack(fill="x", padx=12, pady=(12, 8))
        header.pack_propagate(False)
        
        # Baslik
        title = ctk.CTkLabel(
            header,
            text="DONUSUM KUYRUGU",
            font=FONT_HEADER,
            text_color=COLORS["text_primary"]
        )
        title.pack(side="left")
        
        # Butonlar
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        self.add_folder_btn = ctk.CTkButton(
            btn_frame,
            text="KLASOR",
            font=FONT_BUTTON,
            width=70,
            height=28,
            fg_color=COLORS["bg_panel"],
            hover_color=COLORS["border_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self._add_folder
        )
        self.add_folder_btn.pack(side="right", padx=(4, 0))
        
        self.add_file_btn = ctk.CTkButton(
            btn_frame,
            text="+ DOSYA",
            font=FONT_BUTTON,
            width=80,
            height=28,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_light"],
            text_color="white",
            command=self._add_files
        )
        self.add_file_btn.pack(side="right")
        
        # Dosya listesi
        self.file_list_frame = ctk.CTkScrollableFrame(
            left_panel,
            fg_color=COLORS["bg_darkest"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=4
        )
        self.file_list_frame.pack(fill="both", expand=True, padx=12, pady=4)
        
        # Bos mesaji
        self.empty_label = ctk.CTkLabel(
            self.file_list_frame,
            text="Dosya eklemek icin + DOSYA butonunu kullanin\nveya .schem/.schematic dosyalarini suruklein",
            font=FONT_LABEL,
            text_color=COLORS["text_muted"],
            justify="center"
        )
        self.empty_label.pack(expand=True, pady=40)
        
        # Alt footer
        footer = ctk.CTkFrame(left_panel, fg_color="transparent", height=40)
        footer.pack(fill="x", padx=12, pady=(4, 12))
        footer.pack_propagate(False)
        
        self.remove_btn = ctk.CTkButton(
            footer,
            text="SECILENI KALDIR",
            font=FONT_BUTTON,
            width=120,
            height=28,
            fg_color=COLORS["bg_dark"],
            hover_color="#2a1a1a",
            border_width=1,
            border_color="#5a2a2a",
            text_color=COLORS["error"],
            command=self._remove_selected
        )
        self.remove_btn.pack(side="left")
        
        self.clear_btn = ctk.CTkButton(
            footer,
            text="TUMUNU TEMIZLE",
            font=FONT_BUTTON,
            width=120,
            height=28,
            fg_color=COLORS["bg_dark"],
            hover_color="#2a1a1a",
            border_width=1,
            border_color="#5a2a2a",
            text_color=COLORS["error"],
            command=self._clear_all
        )
        self.clear_btn.pack(side="left", padx=(8, 0))
    
    def _create_right_panel(self):
        """Sag panel - Kontrol"""
        right_panel = ctk.CTkFrame(
            self.content_frame,
            fg_color=COLORS["bg_dark"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=6
        )
        right_panel.grid(row=0, column=2, sticky="nsew")
        
        # Ayarlar bolumu
        settings_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        settings_frame.pack(fill="x", padx=12, pady=12)
        
        # Cikti dizini
        output_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        output_frame.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(
            output_frame,
            text="CIKTI",
            font=FONT_BUTTON,
            text_color=COLORS["text_muted"],
            width=50
        ).pack(side="left")
        
        self.output_entry = ctk.CTkEntry(
            output_frame,
            font=FONT_MONO_SMALL,
            fg_color=COLORS["bg_darkest"],
            border_color=COLORS["border"],
            text_color=COLORS["text_mono"],
            height=28
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.output_entry.insert(0, str(self.output_dir))
        
        self.output_btn = ctk.CTkButton(
            output_frame,
            text="SEC",
            font=FONT_BUTTON,
            width=50,
            height=28,
            fg_color=COLORS["bg_panel"],
            hover_color=COLORS["border_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self._select_output_dir
        )
        self.output_btn.pack(side="right")
        
        # Toggle secenekleri
        toggle_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        toggle_frame.pack(fill="x", pady=(8, 0))
        
        self.overwrite_var = ctk.BooleanVar(value=True)
        self.overwrite_check = ctk.CTkCheckBox(
            toggle_frame,
            text="Mevcut dosyalarin ustune yaz",
            font=FONT_LABEL,
            variable=self.overwrite_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_light"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            checkmark_color="white"
        )
        self.overwrite_check.pack(anchor="w")
        
        self.debug_var = ctk.BooleanVar(value=False)
        self.debug_check = ctk.CTkCheckBox(
            toggle_frame,
            text="Detayli log goster",
            font=FONT_LABEL,
            variable=self.debug_var,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_light"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            checkmark_color="white"
        )
        self.debug_check.pack(anchor="w", pady=(4, 0))
        
        # DONUSTUR butonu
        self.convert_btn = ctk.CTkButton(
            right_panel,
            text="▶   D O N U S T U R",
            font=("Segoe UI", 12, "bold"),
            height=52,
            fg_color=COLORS["btn_convert"],
            hover_color=COLORS["btn_convert_hover"],
            border_width=2,
            border_color=COLORS["btn_convert_border"],
            text_color=COLORS["accent_light"],
            command=self._start_conversion
        )
        self.convert_btn.pack(fill="x", padx=12, pady=(4, 12))
        
        # Genel ilerleme
        progress_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        progress_frame.pack(fill="x", padx=12, pady=(0, 8))
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Genel Ilerleme - 0/0 dosya",
            font=FONT_LABEL,
            text_color=COLORS["text_muted"]
        )
        self.progress_label.pack(anchor="w")
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=6,
            fg_color=COLORS["bg_darkest"],
            progress_color=COLORS["accent"],
            corner_radius=3
        )
        self.progress_bar.pack(fill="x", pady=(4, 0))
        self.progress_bar.set(0)
        
        # Log alani
        log_label = ctk.CTkLabel(
            right_panel,
            text="LOG",
            font=FONT_BUTTON,
            text_color=COLORS["text_muted"]
        )
        log_label.pack(anchor="w", padx=12)
        
        # Log text widget (tk.Text daha iyi renklendirme icin)
        log_frame = ctk.CTkFrame(
            right_panel,
            fg_color=COLORS["bg_darkest"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=4
        )
        log_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        
        self.log_text = tk.Text(
            log_frame,
            font=FONT_MONO,
            bg=COLORS["bg_darkest"],
            fg=COLORS["text_mono"],
            insertbackground=COLORS["text_primary"],
            selectbackground=COLORS["accent"],
            relief="flat",
            padx=8,
            pady=8,
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Log renk tagleri
        self.log_text.tag_configure("timestamp", foreground="#2a4a6a")
        self.log_text.tag_configure("info", foreground=COLORS["accent_light"])
        self.log_text.tag_configure("success", foreground=COLORS["success"])
        self.log_text.tag_configure("warning", foreground=COLORS["warning"])
        self.log_text.tag_configure("error", foreground=COLORS["error"])
        self.log_text.tag_configure("normal", foreground=COLORS["text_mono"])
        
        self.log_text.config(state="disabled")
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Alt footer - istatistikler
        stats_frame = ctk.CTkFrame(right_panel, fg_color="transparent", height=36)
        stats_frame.pack(fill="x", padx=12, pady=(0, 12))
        stats_frame.pack_propagate(False)
        
        # Basarili badge
        self.success_badge = ctk.CTkLabel(
            stats_frame,
            text=" 0 basarili ",
            font=FONT_MONO_SMALL,
            fg_color="#0a2a1a",
            text_color=COLORS["success"],
            corner_radius=10,
            padx=8,
            pady=2
        )
        self.success_badge.pack(side="left")
        
        # Hata badge
        self.error_badge = ctk.CTkLabel(
            stats_frame,
            text=" 0 hata ",
            font=FONT_MONO_SMALL,
            fg_color="#2a1a1a",
            text_color=COLORS["error"],
            corner_radius=10,
            padx=8,
            pady=2
        )
        self.error_badge.pack(side="left", padx=(8, 0))
        
        # Rapor butonu
        self.report_btn = ctk.CTkButton(
            stats_frame,
            text="RAPORU KAYDET",
            font=FONT_BUTTON,
            width=110,
            height=26,
            fg_color=COLORS["bg_panel"],
            hover_color=COLORS["border_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            command=self._save_report
        )
        self.report_btn.pack(side="right")
    
    # =========================================================================
    # DOSYA ISLEMLERI
    # =========================================================================
    def _add_files(self):
        """Dosya ekle dialog"""
        files = filedialog.askopenfilenames(
            title="Schematic Dosyalari Sec",
            filetypes=[
                ("Schematic", "*.schem *.schematic *.litematic"),
                ("Tum Dosyalar", "*.*")
            ]
        )
        for f in files:
            self._add_file_to_queue(Path(f))
    
    def _add_folder(self):
        """Klasor ekle"""
        folder = filedialog.askdirectory(title="Klasor Sec")
        if folder:
            folder_path = Path(folder)
            for ext in ["*.schem", "*.schematic", "*.litematic"]:
                for f in folder_path.glob(ext):
                    self._add_file_to_queue(f)
    
    def _add_file_to_queue(self, path: Path):
        """Dosyayi kuyruga ekle"""
        # Zaten eklenmis mi?
        for item in self.files_queue:
            if item["path"] == path:
                return
        
        self.files_queue.append({
            "path": path,
            "status": FileStatus.PENDING,
            "progress": 0,
            "widget": None
        })
        
        self._refresh_file_list()
    
    def _refresh_file_list(self):
        """Dosya listesini yenile"""
        # Mevcut widgetlari temizle
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        
        if not self.files_queue:
            self.empty_label = ctk.CTkLabel(
                self.file_list_frame,
                text="Dosya eklemek icin + DOSYA butonunu kullanin",
                font=FONT_LABEL,
                text_color=COLORS["text_muted"],
                justify="center"
            )
            self.empty_label.pack(expand=True, pady=40)
            return
        
        for i, item in enumerate(self.files_queue):
            self._create_file_row(item, i)
    
    def _create_file_row(self, item: dict, index: int):
        """Dosya satiri olustur"""
        row = ctk.CTkFrame(
            self.file_list_frame,
            fg_color="transparent",
            height=36
        )
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        
        # Durum ikonu
        status = item["status"]
        if status == FileStatus.SUCCESS:
            icon = "✓"
            color = COLORS["success"]
        elif status == FileStatus.ERROR:
            icon = "✗"
            color = COLORS["error"]
        elif status == FileStatus.PROCESSING:
            icon = "◌"
            color = COLORS["warning"]
        else:
            icon = "○"
            color = COLORS["text_muted"]
        
        icon_label = ctk.CTkLabel(
            row,
            text=f"[{icon}]",
            font=FONT_MONO,
            text_color=color,
            width=30
        )
        icon_label.pack(side="left")
        
        # Dosya adi
        name = item["path"].name
        if len(name) > 28:
            name = name[:25] + "..."
        
        name_label = ctk.CTkLabel(
            row,
            text=name,
            font=FONT_MONO,
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        name_label.pack(side="left", fill="x", expand=True)
        
        # Durum etiketi
        status_text = f"[{status}]"
        status_label = ctk.CTkLabel(
            row,
            text=status_text,
            font=FONT_MONO_SMALL,
            text_color=color,
            width=60
        )
        status_label.pack(side="right")
        
        # Progress bar (islem sirasinda)
        if status == FileStatus.PROCESSING:
            progress = ctk.CTkProgressBar(
                row,
                height=2,
                fg_color=COLORS["bg_dark"],
                progress_color=COLORS["accent"],
                corner_radius=1,
                width=100
            )
            progress.pack(side="right", padx=(0, 8))
            progress.set(item["progress"] / 100)
        
        item["widget"] = row
    
    def _remove_selected(self):
        """Secili dosyayi kaldir (son eklenen)"""
        if self.files_queue:
            self.files_queue.pop()
            self._refresh_file_list()
    
    def _clear_all(self):
        """Tum dosyalari temizle"""
        self.files_queue.clear()
        self._refresh_file_list()
    
    def _select_output_dir(self):
        """Cikti dizini sec"""
        folder = filedialog.askdirectory(title="Cikti Dizini Sec")
        if folder:
            self.output_dir = Path(folder)
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, str(self.output_dir))
    
    # =========================================================================
    # DONUSUM
    # =========================================================================
    def _start_conversion(self):
        """Donusumu baslat"""
        if self.is_converting:
            return
        
        if not self.files_queue:
            messagebox.showwarning("Uyari", "Donusturmek icin dosya ekleyin!")
            return
        
        self.is_converting = True
        self.success_count = 0
        self.error_count = 0
        
        # Butonu devre disi birak
        self.convert_btn.configure(
            text="◌   D O N U S T U R U L U Y O R . . .",
            state="disabled"
        )
        
        # Thread'de calistir
        thread = threading.Thread(target=self._convert_files, daemon=True)
        thread.start()
    
    def _convert_files(self):
        """Dosyalari donustur (thread)"""
        total = len(self.files_queue)
        mapper = BlockMapper()
        
        for i, item in enumerate(self.files_queue):
            # Durumu guncelle
            item["status"] = FileStatus.PROCESSING
            item["progress"] = 0
            self._queue_ui_update()
            
            try:
                path = item["path"]
                self._log(f"Isleniyor: {path.name}", "info")
                
                # Oku
                item["progress"] = 25
                self._queue_ui_update()
                blocks = read_schematic(path)
                self._log(f"  Okunan blok: {len(blocks)}", "normal")
                
                # Donustur
                item["progress"] = 50
                self._queue_ui_update()
                mapped = mapper.map_blocks(blocks)
                self._log(f"  Donusturulen: {len(mapped)}", "normal")
                
                # Yaz
                item["progress"] = 75
                self._queue_ui_update()
                
                output_path = self.output_dir / f"{path.stem}.prefab.json"
                write_prefab(mapped, output_path)
                
                item["progress"] = 100
                item["status"] = FileStatus.SUCCESS
                self.success_count += 1
                self._log(f"  Kaydedildi: {output_path.name}", "success")
                
            except Exception as e:
                item["status"] = FileStatus.ERROR
                self.error_count += 1
                self._log(f"  HATA: {str(e)}", "error")
            
            # Ilerlemeyi guncelle
            progress = (i + 1) / total
            self.log_queue.put(("progress", progress, i + 1, total))
            self._queue_ui_update()
        
        # Tamamlandi
        self.is_converting = False
        self.log_queue.put(("done", None, None, None))
        self._queue_ui_update()
    
    def _queue_ui_update(self):
        """UI guncellemesi icin sinyal gonder"""
        self.log_queue.put(("refresh", None, None, None))
    
    def _log(self, message: str, level: str = "normal"):
        """Log mesaji ekle"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(("log", timestamp, message, level))
    
    def _check_log_queue(self):
        """Log queue'u kontrol et"""
        try:
            while True:
                msg_type, arg1, arg2, arg3 = self.log_queue.get_nowait()
                
                if msg_type == "log":
                    self._add_log_entry(arg1, arg2, arg3)
                elif msg_type == "progress":
                    self.progress_bar.set(arg1)
                    self.progress_label.configure(
                        text=f"Genel Ilerleme - {arg2}/{arg3} dosya"
                    )
                elif msg_type == "refresh":
                    self._refresh_file_list()
                    self._update_stats()
                elif msg_type == "done":
                    self.convert_btn.configure(
                        text="▶   D O N U S T U R",
                        state="normal"
                    )
                    self._log(f"Tamamlandi: {self.success_count} basarili, {self.error_count} hata", 
                             "success" if self.error_count == 0 else "warning")
        except queue.Empty:
            pass
        
        self.after(100, self._check_log_queue)
    
    def _add_log_entry(self, timestamp: str, message: str, level: str):
        """Log satirini ekle"""
        self.log_text.config(state="normal")
        
        # Timestamp
        self.log_text.insert("end", f"[{timestamp}] ", "timestamp")
        
        # Mesaj
        self.log_text.insert("end", f"{message}\n", level)
        
        self.log_text.see("end")
        self.log_text.config(state="disabled")
    
    def _update_stats(self):
        """Istatistikleri guncelle"""
        self.success_badge.configure(text=f" {self.success_count} basarili ")
        self.error_badge.configure(text=f" {self.error_count} hata ")
    
    def _save_report(self):
        """Raporu kaydet"""
        report_path = self.output_dir / f"conversion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("HYTALE CONVERTER - DONUSUM RAPORU\n")
            f.write("=" * 50 + "\n")
            f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Toplam: {len(self.files_queue)} dosya\n")
            f.write(f"Basarili: {self.success_count}\n")
            f.write(f"Hata: {self.error_count}\n")
            f.write("=" * 50 + "\n\n")
            
            for item in self.files_queue:
                status = item["status"]
                f.write(f"[{status}] {item['path'].name}\n")
        
        self._log(f"Rapor kaydedildi: {report_path.name}", "success")
        messagebox.showinfo("Rapor", f"Rapor kaydedildi:\n{report_path}")


# =============================================================================
# MAIN
# =============================================================================
def run():
    """Uygulamayi baslat"""
    app = HytaleConverterApp()
    app.mainloop()


if __name__ == "__main__":
    run()
