"""GUI icin tekrar kullanilabilir bilesenler."""

from __future__ import annotations

import customtkinter as ctk


class QueueItemWidget(ctk.CTkFrame):
    """Dosya kuyrugundaki tek satiri gosteren bilesen."""

    def __init__(self, master, file_name: str, on_select) -> None:
        """Kuyruk satirini ikon, dosya adi ve progress bar ile olusturur."""
        super().__init__(master, corner_radius=10)
        self.on_select = on_select
        self._selected = False

        self.status_label = ctk.CTkLabel(self, text="⏳", width=24)
        self.status_label.grid(row=0, column=0, padx=(8, 4), pady=(8, 2), sticky="w")

        self.file_label = ctk.CTkLabel(self, text=file_name, anchor="w")
        self.file_label.grid(row=0, column=1, padx=(0, 8), pady=(8, 2), sticky="ew")

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.grid(row=1, column=0, columnspan=2, padx=8, pady=(2, 8), sticky="ew")

        self.grid_columnconfigure(1, weight=1)

        # Satir secimini kolaylastirmak icin tum parcalara click eventi baglanir.
        self.bind("<Button-1>", self._handle_click)
        self.file_label.bind("<Button-1>", self._handle_click)
        self.status_label.bind("<Button-1>", self._handle_click)
        self.progress.bind("<Button-1>", self._handle_click)

    def _handle_click(self, _event) -> None:
        """Satir secildiginde parent'a secim bilgisini iletir."""
        self.on_select(self)

    def set_status(self, icon: str) -> None:
        """Durum ikonunu gunceller."""
        self.status_label.configure(text=icon)

    def set_progress(self, value: float) -> None:
        """0-1 arasi progress degerini satir bazinda gunceller."""
        self.progress.set(max(0.0, min(1.0, value)))

    def set_selected(self, selected: bool) -> None:
        """Satirin secili gorsel stilini acip kapatir."""
        self._selected = selected
        fg = ("#2F6AA8", "#1F538D") if selected else ("#3A3A3A", "#2B2B2B")
        self.configure(fg_color=fg)

    @property
    def is_selected(self) -> bool:
        """Satirin secili olup olmadigini doner."""
        return self._selected
