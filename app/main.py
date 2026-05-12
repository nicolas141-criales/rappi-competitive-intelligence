"""
main.py - Punto de entrada del sistema de Competitive Intelligence.

Uso:
    python app/main.py                    # scraping completo (todas las plataformas)
    python app/main.py --mock             # genera datos mock sin scraping real
    python app/main.py --platform rappi  # solo una plataforma
    python app/main.py --addresses 5     # limitar direcciones
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Forzar UTF-8 en la consola Windows para evitar UnicodeEncodeError
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from app.analytics.insights import generate_executive_insights, get_kpis
from app.core.config import (
    CDMX_ADDRESSES,
    COMPETITIVE_CSV,
    COMPETITIVE_JSON,
    PLATFORMS,
)
from app.core.logger import logger
from app.core.utils import load_data, save_raw_csv, save_raw_json

console = Console(force_terminal=True, highlight=False)


# ── Mock data generator ───────────────────────────────────────────────────────

def generate_mock_data(addresses: list[dict], platforms: list[str]) -> list[dict]:
    """Genera datos simulados sin necesidad de Playwright."""
    from app.scrapers.rappi_scraper import RappiScraper
    from app.scrapers.uber_scraper  import UberEatsScraper
    from app.scrapers.didi_scraper  import DiDiScraper

    scraper_map = {
        "rappi":    RappiScraper(),
        "ubereats": UberEatsScraper(),
        "didi":     DiDiScraper(),
    }
    all_records: list[dict] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        for plt in platforms:
            scraper = scraper_map.get(plt)
            if not scraper:
                continue
            task = progress.add_task(
                f"[cyan]Generando datos {plt.title()}...", total=len(addresses)
            )
            for addr in addresses:
                records = scraper._generate_simulated_records(addr)
                all_records.extend(records)
                progress.advance(task)

    return all_records


# ── Live scraping ─────────────────────────────────────────────────────────────

async def run_scrapers(addresses: list[dict], platforms: list[str]) -> list[dict]:
    from app.scrapers.rappi_scraper import RappiScraper
    from app.scrapers.uber_scraper  import UberEatsScraper
    from app.scrapers.didi_scraper  import DiDiScraper

    scraper_map = {
        "rappi":    RappiScraper(),
        "ubereats": UberEatsScraper(),
        "didi":     DiDiScraper(),
    }
    all_records: list[dict] = []

    for plt in platforms:
        scraper = scraper_map.get(plt)
        if not scraper:
            logger.warning(f"No scraper found for platform: {plt}")
            continue
        logger.info(f"Starting scraper: {plt}")
        records = await scraper.run(addresses)
        all_records.extend(records)

    return all_records


# ── Save addresses CSV ────────────────────────────────────────────────────────

def save_addresses(addresses: list[dict]):
    import pandas as pd
    from app.core.config import DATA_DIR
    path = DATA_DIR / "addresses.csv"
    pd.DataFrame(addresses).to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"Addresses saved -> {path}")


# ── Print summary table ───────────────────────────────────────────────────────

def print_summary(df):
    if df.empty:
        return
    kpis = get_kpis(df)

    table = Table(
        title="Resumen Ejecutivo Competitive Intelligence",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Metrica",    style="cyan", no_wrap=True)
    table.add_column("Rappi",      justify="right", style="red")
    table.add_column("Uber Eats",  justify="right", style="green")
    table.add_column("DiDi Food",  justify="right", style="yellow")

    afp = kpis.get("avg_final_price",  {})
    adf = kpis.get("avg_delivery_fee", {})
    asf = kpis.get("avg_service_fee",  {})
    eta = kpis.get("avg_eta_min",      {})
    fdr = kpis.get("free_delivery_rate", {})
    pro = kpis.get("promo_intensity",  {})

    for label, d, fmt in [
        ("Precio Final Prom. (MXN)", afp, "price"),
        ("Delivery Fee Prom. (MXN)", adf, "price"),
        ("Service Fee Prom. (MXN)",  asf, "price"),
        ("ETA Promedio (min)",        eta, "float"),
        ("Envio Gratis (%)",          fdr, "float"),
        ("Con Promocion (%)",         pro, "float"),
    ]:
        def fmt_val(val, f):
            if f == "price":
                return f"${val:.2f}"
            return f"{val:.1f}"

        table.add_row(
            label,
            fmt_val(d.get("rappi",    0), fmt),
            fmt_val(d.get("ubereats", 0), fmt),
            fmt_val(d.get("didi",     0), fmt),
        )

    console.print(table)

    # Imprimir diferencias vs Rappi
    diffs = kpis.get("rappi_price_vs_competition", {})
    console.print("\n[bold]Diferencia de precio final vs Rappi:[/bold]")
    for plat, diff in diffs.items():
        sign   = "+" if diff > 0 else ""
        color  = "green" if diff < 0 else "red"
        console.print(f"  {plat.title()}: [{color}]{sign}{diff:.1f}%[/{color}]")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Rappi Competitive Intelligence Scraper")
    p.add_argument("--mock",        action="store_true", help="Usar datos simulados")
    p.add_argument("--platform",    type=str, default=None,
                   help="Plataforma: rappi|ubereats|didi")
    p.add_argument("--addresses",   type=int, default=None,
                   help="Numero de direcciones a usar")
    p.add_argument("--no-insights", action="store_true",
                   help="Omitir generacion de insights")
    return p.parse_args()


def main():
    args = parse_args()

    console.print(Panel.fit(
        "[bold red]>>> Rappi Competitive Intelligence System <<<[/bold red]\n"
        "[dim]AI Engineer | Analisis Competitivo CDMX[/dim]",
        border_style="red",
    ))

    platforms = [args.platform] if args.platform else PLATFORMS
    addresses = CDMX_ADDRESSES[: args.addresses] if args.addresses else CDMX_ADDRESSES
    save_addresses(addresses)

    console.print(f"\n[bold]Plataformas:[/bold] {', '.join(platforms)}")
    console.print(f"[bold]Direcciones:[/bold] {len(addresses)}")
    console.print(f"[bold]Modo:[/bold] {'Simulado (Mock)' if args.mock else 'Live Scraping'}\n")

    # ── Ejecutar scraping ──────────────────────────────────────────────────────
    if args.mock:
        all_records = generate_mock_data(addresses, platforms)
    else:
        console.print("[yellow]Iniciando Playwright...[/yellow]")
        all_records = asyncio.run(run_scrapers(addresses, platforms))

    if not all_records:
        console.print("[red]ERROR: No se obtuvieron datos. Verifica logs.[/red]")
        sys.exit(1)

    # ── Guardar datos ──────────────────────────────────────────────────────────
    save_raw_csv(all_records, COMPETITIVE_CSV)
    save_raw_json(all_records, COMPETITIVE_JSON)

    console.print(f"\n[green]OK: {len(all_records)} registros guardados[/green]")
    console.print(f"  CSV:  {COMPETITIVE_CSV}")
    console.print(f"  JSON: {COMPETITIVE_JSON}")

    # ── Insights ───────────────────────────────────────────────────────────────
    if not args.no_insights:
        console.print("\n[bold cyan]Generando insights ejecutivos...[/bold cyan]")
        df       = load_data(COMPETITIVE_CSV)
        insights = generate_executive_insights(df)
        console.print(f"[green]OK: {len(insights)} insights generados[/green]")
        print_summary(df)

    console.print(Panel.fit(
        "[bold green]>> Proceso completado <<[/bold green]\n"
        "[dim]Ejecuta: streamlit run app/dashboard/dashboard.py[/dim]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
