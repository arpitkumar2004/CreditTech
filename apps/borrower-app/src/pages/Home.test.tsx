import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Home from "./Home";

describe("Home (Overview)", () => {
  it("renders the overview heading with officer greeting", () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );
    expect(screen.getByRole("heading", { level: 1, name: /Overview/i })).toBeInTheDocument();
  });

  it("shows key portfolio metrics", () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );
    expect(screen.getAllByText(/Cumulative disbursement/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Active borrowers/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Pending review/i).length).toBeGreaterThan(0);
  });

  it("shows recent applications table with rows", () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );
    expect(screen.getByText(/Recent applications/i)).toBeInTheDocument();
    // 6 recent rows
    const rows = screen.getAllByRole("row");
    // 1 header row + 6 data rows = 7
    expect(rows.length).toBe(7);
  });
});
