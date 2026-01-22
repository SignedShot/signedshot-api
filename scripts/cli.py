#!/usr/bin/env python3
"""CLI for testing SignedShot API."""

import httpx
import typer

app = typer.Typer(help="SignedShot API testing CLI")

DEFAULT_BASE_URL = "http://localhost:8000"


@app.command()
def register(
    device_id: str = typer.Argument(..., help="Device ID to register"),
    base_url: str = typer.Option(DEFAULT_BASE_URL, "--url", "-u", help="API base URL"),
) -> None:
    """Register a new device and get a token."""
    url = f"{base_url}/devices/register"

    typer.echo(f"Registering device: {device_id}")
    typer.echo(f"URL: {url}")

    try:
        response = httpx.post(url, json={"device_id": device_id})

        if response.status_code == 201:
            data = response.json()
            typer.echo(typer.style("\nSuccess!", fg=typer.colors.GREEN, bold=True))
            typer.echo(f"Device Token: {data['device_token']}")
            typer.echo(f"Created At: {data['created_at']}")
            typer.echo(
                typer.style(
                    "\nStore this token securely - it cannot be retrieved again!",
                    fg=typer.colors.YELLOW,
                )
            )
        elif response.status_code == 409:
            typer.echo(
                typer.style("\nDevice already registered", fg=typer.colors.RED),
                err=True,
            )
            raise typer.Exit(1)
        elif response.status_code == 422:
            typer.echo(
                typer.style("\nValidation error", fg=typer.colors.RED),
                err=True,
            )
            typer.echo(response.json())
            raise typer.Exit(1)
        else:
            typer.echo(
                typer.style(f"\nError: {response.status_code}", fg=typer.colors.RED),
                err=True,
            )
            typer.echo(response.text)
            raise typer.Exit(1)

    except httpx.ConnectError:
        typer.echo(
            typer.style(
                f"\nCould not connect to {base_url}. Is the server running?",
                fg=typer.colors.RED,
            ),
            err=True,
        )
        raise typer.Exit(1) from None


@app.command()
def session(
    token: str = typer.Argument(..., help="Device token from registration"),
    base_url: str = typer.Option(DEFAULT_BASE_URL, "--url", "-u", help="API base URL"),
) -> None:
    """Create a capture session using device token."""
    url = f"{base_url}/capture/session"

    typer.echo("Creating capture session...")
    typer.echo(f"URL: {url}")

    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 201:
            data = response.json()
            typer.echo(typer.style("\nSuccess!", fg=typer.colors.GREEN, bold=True))
            typer.echo(f"Capture ID: {data['capture_id']}")
            typer.echo(f"Nonce: {data['nonce']}")
            typer.echo(f"Expires At: {data['expires_at']}")
        elif response.status_code == 401:
            typer.echo(
                typer.style("\nInvalid device token", fg=typer.colors.RED),
                err=True,
            )
            raise typer.Exit(1)
        else:
            typer.echo(
                typer.style(f"\nError: {response.status_code}", fg=typer.colors.RED),
                err=True,
            )
            typer.echo(response.text)
            raise typer.Exit(1)

    except httpx.ConnectError:
        typer.echo(
            typer.style(
                f"\nCould not connect to {base_url}. Is the server running?",
                fg=typer.colors.RED,
            ),
            err=True,
        )
        raise typer.Exit(1) from None


@app.command()
def trust(
    nonce: str = typer.Argument(..., help="Nonce from capture session"),
    base_url: str = typer.Option(DEFAULT_BASE_URL, "--url", "-u", help="API base URL"),
) -> None:
    """Generate a trust token using the capture session nonce."""
    url = f"{base_url}/capture/trust"

    typer.echo("Generating trust token...")
    typer.echo(f"URL: {url}")

    try:
        response = httpx.post(url, json={"nonce": nonce})

        if response.status_code == 200:
            data = response.json()
            typer.echo(typer.style("\nSuccess!", fg=typer.colors.GREEN, bold=True))
            typer.echo(f"Trust Token: {data['trust_token']}")
        elif response.status_code == 400:
            typer.echo(
                typer.style("\nInvalid or expired nonce", fg=typer.colors.RED),
                err=True,
            )
            raise typer.Exit(1)
        else:
            typer.echo(
                typer.style(f"\nError: {response.status_code}", fg=typer.colors.RED),
                err=True,
            )
            typer.echo(response.text)
            raise typer.Exit(1)

    except httpx.ConnectError:
        typer.echo(
            typer.style(
                f"\nCould not connect to {base_url}. Is the server running?",
                fg=typer.colors.RED,
            ),
            err=True,
        )
        raise typer.Exit(1) from None


@app.command()
def health(
    base_url: str = typer.Option(DEFAULT_BASE_URL, "--url", "-u", help="API base URL"),
) -> None:
    """Check API health."""
    url = f"{base_url}/health"

    try:
        response = httpx.get(url)

        if response.status_code == 200:
            typer.echo(typer.style("API is healthy", fg=typer.colors.GREEN))
        else:
            typer.echo(
                typer.style(f"API returned {response.status_code}", fg=typer.colors.RED)
            )
            raise typer.Exit(1)

    except httpx.ConnectError:
        typer.echo(
            typer.style(
                f"Could not connect to {base_url}",
                fg=typer.colors.RED,
            ),
            err=True,
        )
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()
