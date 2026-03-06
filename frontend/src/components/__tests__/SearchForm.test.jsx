import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchForm from '../SearchForm';

describe('SearchForm Component', () => {
  const mockOnResults = jest.fn();
  const mockOnLoading = jest.fn();

  beforeEach(() => {
    mockOnResults.mockClear();
    mockOnLoading.mockClear();
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders all input fields', () => {
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      expect(screen.getByDisplayValue('')).toBeInTheDocument();
      expect(screen.getByText('Marque')).toBeInTheDocument();
      expect(screen.getByText('Modèle')).toBeInTheDocument();
      expect(screen.getByText('Boîte de vitesses')).toBeInTheDocument();
      expect(screen.getByText('Prix min')).toBeInTheDocument();
      expect(screen.getByText('Prix max')).toBeInTheDocument();
      expect(screen.getByText('Kilométrage max')).toBeInTheDocument();
      expect(screen.getByText('Année min')).toBeInTheDocument();
      expect(screen.getByText('Chevaux min')).toBeInTheDocument();
      expect(screen.getByText('Chevaux max')).toBeInTheDocument();
    });

    it('renders submit button with text "Chercher"', () => {
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);
      const button = screen.getByRole('button', { name: /chercher/i });
      expect(button).toBeInTheDocument();
    });

    it('renders PatternSelector component', () => {
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);
      expect(screen.getByText(/motifs/i) || screen.getByText(/pattern/i)).toBeInTheDocument();
    });
  });

  describe('Form Input Handling', () => {
    it('updates form state when typing in brand input', async () => {
      const user = userEvent.setup();
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const brandInput = screen.getByPlaceholderText('ex: Peugeot');
      await user.type(brandInput, 'Renault');
      expect(brandInput).toHaveValue('Renault');
    });

    it('updates form state when typing in model input', async () => {
      const user = userEvent.setup();
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const modelInput = screen.getByPlaceholderText('ex: 308');
      await user.type(modelInput, 'Clio');
      expect(modelInput).toHaveValue('Clio');
    });

    it('updates numeric fields correctly', async () => {
      const user = userEvent.setup();
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const priceMinInput = screen.getByPlaceholderText('0');
      await user.type(priceMinInput, '5000');
      expect(priceMinInput).toHaveValue(5000);
    });
  });

  describe('Submit Behavior', () => {
    it('shows loading state while searching', async () => {
      const user = userEvent.setup();
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const submitButton = screen.getByRole('button', { name: /chercher/i });
      const brandInput = screen.getByPlaceholderText('ex: Peugeot');

      await user.type(brandInput, 'Peugeot');
      await user.click(submitButton);

      expect(mockOnLoading).toHaveBeenCalledWith(true);
    });

    it('calls onLoading(false) after search completes', async () => {
      const user = userEvent.setup();
      const { searchListings } = require('../../api/client');
      searchListings.mockResolvedValueOnce({ listings: [] });

      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const submitButton = screen.getByRole('button', { name: /chercher/i });
      const brandInput = screen.getByPlaceholderText('ex: Peugeot');

      await user.type(brandInput, 'Peugeot');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnLoading).toHaveBeenCalledWith(false);
      });
    });

    it('calls searchListings with correct payload', async () => {
      const user = userEvent.setup();
      const { searchListings } = require('../../api/client');
      searchListings.mockResolvedValueOnce({ listings: [] });

      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const brandInput = screen.getByPlaceholderText('ex: Peugeot');
      const modelInput = screen.getByPlaceholderText('ex: 308');
      const submitButton = screen.getByRole('button', { name: /chercher/i });

      await user.type(brandInput, 'Renault');
      await user.type(modelInput, 'Clio');
      await user.click(submitButton);

      await waitFor(() => {
        expect(searchListings).toHaveBeenCalledWith(
          expect.objectContaining({
            brand: 'Renault',
            model: 'Clio',
          })
        );
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message when API call fails', async () => {
      const user = userEvent.setup();
      const { searchListings } = require('../../api/client');
      const errorMessage = 'API Error: Server not available';
      searchListings.mockRejectedValueOnce(new Error(errorMessage));

      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const brandInput = screen.getByPlaceholderText('ex: Peugeot');
      const submitButton = screen.getByRole('button', { name: /chercher/i });

      await user.type(brandInput, 'Renault');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it('calls onResults(null) when search fails', async () => {
      const user = userEvent.setup();
      const { searchListings } = require('../../api/client');
      searchListings.mockRejectedValueOnce(new Error('Network error'));

      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const brandInput = screen.getByPlaceholderText('ex: Peugeot');
      const submitButton = screen.getByRole('button', { name: /chercher/i });

      await user.type(brandInput, 'Renault');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnResults).toHaveBeenCalledWith(null);
      });
    });
  });
});
