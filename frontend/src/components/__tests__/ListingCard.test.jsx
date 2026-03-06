import { render, screen } from '@testing-library/react';
import ListingCard from '../ListingCard';

describe('ListingCard Component', () => {
  const mockListing = {
    title: 'Renault Clio 2015 - Très bon état',
    price: 4500,
    year: 2015,
    mileage: 95000,
    location: 'Paris (75)',
    url: 'https://example.com/listing/1',
    matched_keywords: ['CT valide', 'Premier propriétaire'],
    vehicle: {
      reliability_score: 7.5,
      common_issues: ['Problème alternateur possible', 'Joint moteur à vérifier'],
    },
  };

  describe('Rendering', () => {
    it('renders listing title', () => {
      render(<ListingCard listing={mockListing} />);
      expect(screen.getByText('Renault Clio 2015 - Très bon état')).toBeInTheDocument();
    });

    it('renders price formatted with space thousands separator', () => {
      render(<ListingCard listing={mockListing} />);
      expect(screen.getByText(/4 500|4500/)).toBeInTheDocument();
    });

    it('renders year', () => {
      render(<ListingCard listing={mockListing} />);
      expect(screen.getByText('2015')).toBeInTheDocument();
    });

    it('renders mileage formatted with unit', () => {
      render(<ListingCard listing={mockListing} />);
      expect(screen.getByText(/95 000|95000/)).toBeInTheDocument();
    });

    it('renders location', () => {
      render(<ListingCard listing={mockListing} />);
      expect(screen.getByText('Paris (75)')).toBeInTheDocument();
    });

    it('renders "Voir l\'annonce" button with external link', () => {
      render(<ListingCard listing={mockListing} />);
      const link = screen.getByRole('link', { name: /voir l'annonce/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', mockListing.url);
      expect(link).toHaveAttribute('target', '_blank');
    });
  });

  describe('Keywords Display', () => {
    it('renders all matched keywords as badges', () => {
      render(<ListingCard listing={mockListing} />);
      expect(screen.getByText('CT valide')).toBeInTheDocument();
      expect(screen.getByText('Premier propriétaire')).toBeInTheDocument();
    });

    it('renders no keywords section when list is empty', () => {
      const listing = { ...mockListing, matched_keywords: [] };
      render(<ListingCard listing={listing} />);
      expect(screen.queryByText('CT valide')).not.toBeInTheDocument();
    });

    it('handles null matched_keywords gracefully', () => {
      const listing = { ...mockListing, matched_keywords: null };
      render(<ListingCard listing={listing} />);
      expect(screen.getByText('Renault Clio 2015 - Très bon état')).toBeInTheDocument();
    });
  });

  describe('Missing Data Handling', () => {
    it('renders with minimal data (title only)', () => {
      const minimal = { title: 'Voiture', url: 'https://example.com' };
      render(<ListingCard listing={minimal} />);
      expect(screen.getByText('Voiture')).toBeInTheDocument();
    });

    it('renders "Annonce sans titre" when title is missing', () => {
      const listing = { ...mockListing, title: null };
      render(<ListingCard listing={listing} />);
      expect(screen.getByText('Annonce sans titre')).toBeInTheDocument();
    });

    it('handles missing price gracefully', () => {
      const listing = { ...mockListing, price: null };
      render(<ListingCard listing={listing} />);
      expect(screen.getByText('Renault Clio 2015 - Très bon état')).toBeInTheDocument();
    });

    it('handles missing year gracefully', () => {
      const listing = { ...mockListing, year: null };
      render(<ListingCard listing={listing} />);
      expect(screen.getByText('Paris (75)')).toBeInTheDocument();
    });
  });

  describe('VehicleScore Integration', () => {
    it('renders VehicleScore component with vehicle data', () => {
      render(<ListingCard listing={mockListing} />);
      expect(screen.getByText(/7.5\/10/)).toBeInTheDocument();
    });

    it('renders common issues from vehicle data', () => {
      render(<ListingCard listing={mockListing} />);
      expect(screen.getByText(/Problème alternateur possible/)).toBeInTheDocument();
      expect(screen.getByText(/Joint moteur à vérifier/)).toBeInTheDocument();
    });

    it('handles missing vehicle data gracefully', () => {
      const listing = { ...mockListing, vehicle: null };
      render(<ListingCard listing={listing} />);
      expect(screen.getByText('Renault Clio 2015 - Très bon état')).toBeInTheDocument();
    });

    it('shows fallback message when no common issues', () => {
      const listing = {
        ...mockListing,
        vehicle: { reliability_score: 8.0, common_issues: null },
      };
      render(<ListingCard listing={listing} />);
      expect(screen.getByText(/données fiabilité/i)).toBeInTheDocument();
    });
  });
});
