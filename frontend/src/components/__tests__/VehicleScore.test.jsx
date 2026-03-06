import { render, screen } from '@testing-library/react';
import VehicleScore from '../VehicleScore';

describe('VehicleScore Component', () => {
  describe('Score Display', () => {
    it('renders score with /10 fiabilité text', () => {
      const vehicle = {
        reliability_score: 8.5,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('8.5/10 fiabilité')).toBeInTheDocument();
    });

    it('renders score with integer value', () => {
      const vehicle = {
        reliability_score: 7,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('7/10 fiabilité')).toBeInTheDocument();
    });

    it('renders N/A badge when score is null', () => {
      const vehicle = {
        reliability_score: null,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });

    it('renders N/A badge when score is undefined', () => {
      const vehicle = {
        reliability_score: undefined,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });

    it('renders N/A when vehicle is null', () => {
      render(<VehicleScore vehicle={null} />);
      expect(screen.queryByText(/fiabilité/i)).not.toBeInTheDocument();
    });

    it('renders N/A when vehicle is undefined', () => {
      render(<VehicleScore vehicle={undefined} />);
      expect(screen.queryByText(/fiabilité/i)).not.toBeInTheDocument();
    });
  });

  describe('Badge Variant (Color)', () => {
    it('renders green badge for score >= 7', () => {
      const vehicle = {
        reliability_score: 7,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('7/10 fiabilité')).toBeInTheDocument();
    });

    it('renders green badge for score > 7', () => {
      const vehicle = {
        reliability_score: 8.5,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('8.5/10 fiabilité')).toBeInTheDocument();
    });

    it('renders orange/warning badge for score 4-6', () => {
      const vehicle = {
        reliability_score: 5,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('5/10 fiabilité')).toBeInTheDocument();
    });

    it('renders orange/warning badge for score 4', () => {
      const vehicle = {
        reliability_score: 4,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('4/10 fiabilité')).toBeInTheDocument();
    });

    it('renders red/danger badge for score < 4', () => {
      const vehicle = {
        reliability_score: 3,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('3/10 fiabilité')).toBeInTheDocument();
    });

    it('renders red/danger badge for score 0', () => {
      const vehicle = {
        reliability_score: 0,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('0/10 fiabilité')).toBeInTheDocument();
    });

    it('renders default badge for null score', () => {
      const vehicle = {
        reliability_score: null,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });

  describe('Common Issues Display', () => {
    it('renders all common issues as bullets', () => {
      const vehicle = {
        reliability_score: 6,
        common_issues: [
          'Problème alternateur',
          'Joint moteur usé',
          'Plaquettes freins à changer',
        ],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText(/Problème alternateur/)).toBeInTheDocument();
      expect(screen.getByText(/Joint moteur usé/)).toBeInTheDocument();
      expect(screen.getByText(/Plaquettes freins à changer/)).toBeInTheDocument();
    });

    it('limits display to first 3 issues', () => {
      const vehicle = {
        reliability_score: 5,
        common_issues: [
          'Issue 1',
          'Issue 2',
          'Issue 3',
          'Issue 4 - Should not appear',
          'Issue 5 - Should not appear',
        ],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText(/Issue 1/)).toBeInTheDocument();
      expect(screen.getByText(/Issue 2/)).toBeInTheDocument();
      expect(screen.getByText(/Issue 3/)).toBeInTheDocument();
      expect(screen.queryByText(/Issue 4/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Issue 5/)).not.toBeInTheDocument();
    });

    it('shows fallback message when no issues', () => {
      const vehicle = {
        reliability_score: 8,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText(/données fiabilité/i)).toBeInTheDocument();
    });

    it('shows fallback message when issues is null', () => {
      const vehicle = {
        reliability_score: 8,
        common_issues: null,
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText(/données fiabilité/i)).toBeInTheDocument();
    });

    it('shows fallback message when issues is undefined', () => {
      const vehicle = {
        reliability_score: 8,
        common_issues: undefined,
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText(/données fiabilité/i)).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty vehicle object', () => {
      render(<VehicleScore vehicle={{}} />);
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });

    it('handles extreme score values', () => {
      const vehicle = {
        reliability_score: 9.9,
        common_issues: [],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText('9.9/10 fiabilité')).toBeInTheDocument();
    });

    it('handles single issue', () => {
      const vehicle = {
        reliability_score: 6,
        common_issues: ['Only one issue'],
      };
      render(<VehicleScore vehicle={vehicle} />);
      expect(screen.getByText(/Only one issue/)).toBeInTheDocument();
    });
  });
});
