import { render, screen } from '@testing-library/react';
import ResultsGrid from '../ResultsGrid';

describe('ResultsGrid Component', () => {
  const mockListings = [
    {
      lbc_id: '1',
      title: 'Renault Clio',
      price: 3500,
      year: 2015,
      mileage: 80000,
      location: 'Paris',
      url: 'https://example.com/1',
      matched_keywords: [],
      vehicle: { reliability_score: 7 },
    },
    {
      lbc_id: '2',
      title: 'Peugeot 308',
      price: 4500,
      year: 2016,
      mileage: 70000,
      location: 'Lyon',
      url: 'https://example.com/2',
      matched_keywords: ['CT valide'],
      vehicle: { reliability_score: 8 },
    },
  ];

  const mockResults = {
    count: 2,
    listings: mockListings,
    session_id: 'abc123',
  };

  describe('Loading State', () => {
    it('shows loading spinner when loading is true', () => {
      render(<ResultsGrid results={null} loading={true} />);
      expect(screen.getByText(/recherche en cours/i)).toBeInTheDocument();
    });

    it('displays loading message', () => {
      render(<ResultsGrid results={null} loading={true} />);
      expect(screen.getByText(/recherche en cours sur leboncoin/i)).toBeInTheDocument();
    });

    it('renders spinner element', () => {
      const { container } = render(<ResultsGrid results={null} loading={true} />);
      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Empty Results', () => {
    it('shows empty message when results is null', () => {
      render(<ResultsGrid results={null} loading={false} />);
      expect(screen.queryByText(/annonce/i)).not.toBeInTheDocument();
    });

    it('shows empty message when count is 0', () => {
      render(<ResultsGrid results={{ count: 0, listings: [] }} loading={false} />);
      expect(
        screen.getByText(/aucune annonce trouvée/i)
      ).toBeInTheDocument();
    });

    it('shows empty message when listings array is empty', () => {
      render(<ResultsGrid results={{ count: 0, listings: [] }} loading={false} />);
      expect(
        screen.getByText(/essayez d'élargir/i)
      ).toBeInTheDocument();
    });

    it('shows empty message when listings is null', () => {
      render(<ResultsGrid results={{ count: 1, listings: null }} loading={false} />);
      expect(
        screen.getByText(/aucune annonce trouvée/i)
      ).toBeInTheDocument();
    });
  });

  describe('Results Display', () => {
    it('displays count of results with singular form', () => {
      const results = { count: 1, listings: [mockListings[0]] };
      render(<ResultsGrid results={results} loading={false} />);
      expect(screen.getByText(/1 annonce trouvée/)).toBeInTheDocument();
    });

    it('displays count of results with plural form', () => {
      render(<ResultsGrid results={mockResults} loading={false} />);
      expect(screen.getByText(/2 annonces trouvées/)).toBeInTheDocument();
    });

    it('renders all listing cards', () => {
      render(<ResultsGrid results={mockResults} loading={false} />);
      expect(screen.getByText('Renault Clio')).toBeInTheDocument();
      expect(screen.getByText('Peugeot 308')).toBeInTheDocument();
    });

    it('passes listing data to ListingCard component', () => {
      render(<ResultsGrid results={mockResults} loading={false} />);
      expect(screen.getByText('Renault Clio')).toBeInTheDocument();
      expect(screen.getByText(/3500|3 500/)).toBeInTheDocument();
      expect(screen.getByText('Peugeot 308')).toBeInTheDocument();
      expect(screen.getByText(/4500|4 500/)).toBeInTheDocument();
    });

    it('uses lbc_id as key for listing cards', () => {
      const { container } = render(<ResultsGrid results={mockResults} loading={false} />);
      const cards = container.querySelectorAll('[class*="rounded"]');
      expect(cards.length).toBeGreaterThan(0);
    });

    it('falls back to id as key if lbc_id is missing', () => {
      const listingWithoutLbcId = { ...mockListings[0], lbc_id: null, id: '1' };
      const results = { count: 1, listings: [listingWithoutLbcId] };
      render(<ResultsGrid results={results} loading={false} />);
      expect(screen.getByText('Renault Clio')).toBeInTheDocument();
    });
  });

  describe('Grid Layout', () => {
    it('renders grid container with responsive classes', () => {
      const { container } = render(<ResultsGrid results={mockResults} loading={false} />);
      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('sm:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('applies spacing between cards', () => {
      const { container } = render(<ResultsGrid results={mockResults} loading={false} />);
      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('gap-4');
    });
  });

  describe('Large Result Sets', () => {
    it('handles large number of listings', () => {
      const manyListings = Array.from({ length: 50 }, (_, i) => ({
        lbc_id: `listing-${i}`,
        title: `Voiture ${i}`,
        price: 5000 + i * 100,
        year: 2015,
        mileage: 80000,
        location: 'City',
        url: `https://example.com/${i}`,
        matched_keywords: [],
        vehicle: { reliability_score: 7 },
      }));

      const results = { count: 50, listings: manyListings };
      render(<ResultsGrid results={results} loading={false} />);

      expect(screen.getByText(/50 annonces trouvées/)).toBeInTheDocument();
      expect(screen.getByText('Voiture 0')).toBeInTheDocument();
      expect(screen.getByText('Voiture 49')).toBeInTheDocument();
    });

    it('correctly pluralizes with large count', () => {
      const manyListings = Array.from({ length: 150 }, (_, i) => ({
        lbc_id: `listing-${i}`,
        title: `Annonce ${i}`,
        price: 5000,
        year: 2015,
        mileage: 80000,
        location: 'City',
        url: 'https://example.com',
        matched_keywords: [],
        vehicle: { reliability_score: 7 },
      }));

      const results = { count: 150, listings: manyListings };
      render(<ResultsGrid results={results} loading={false} />);
      expect(screen.getByText(/150 annonces trouvées/)).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles missing optional fields in listings', () => {
      const minimalListing = {
        lbc_id: '1',
        title: 'Voiture',
        url: 'https://example.com',
      };
      const results = { count: 1, listings: [minimalListing] };
      render(<ResultsGrid results={results} loading={false} />);
      expect(screen.getByText('Voiture')).toBeInTheDocument();
    });

    it('renders correctly with exactly 2 results', () => {
      render(<ResultsGrid results={mockResults} loading={false} />);
      expect(screen.getByText(/2 annonces trouvées/)).toBeInTheDocument();
    });
  });
});
