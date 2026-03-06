import * as clientModule from '../../api/client';

describe('API Client', () => {
  let originalFetch;

  beforeAll(() => {
    originalFetch = global.fetch;
  });

  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  afterAll(() => {
    global.fetch = originalFetch;
  });

  describe('searchListings', () => {
    it('calls API with correct method and headers', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValueOnce({ listings: [] }),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { searchListings } = require('../../api/client');
      const params = { brand: 'Renault', model: 'Clio' };
      
      await searchListings(params);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/search'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });

    it('sends payload as JSON body', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValueOnce({ listings: [] }),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { searchListings } = require('../../api/client');
      const params = { brand: 'Peugeot', price_min: 5000 };
      
      await searchListings(params);

      const callBody = JSON.parse(global.fetch.mock.calls[0][1].body);
      expect(callBody).toEqual(params);
    });

    it('returns parsed response on success', async () => {
      const mockData = { listings: [{ id: '1', title: 'Car' }] };
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValueOnce(mockData),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { searchListings } = require('../../api/client');
      const result = await searchListings({});
      
      expect(result).toEqual(mockData);
    });

    it('throws error on HTTP failure', async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValueOnce({ detail: 'Brand required' }),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { searchListings } = require('../../api/client');
      
      await expect(searchListings({})).rejects.toThrow('Brand required');
    });

    it('uses status code in error if no detail', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        json: jest.fn().mockResolvedValueOnce({}),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { searchListings } = require('../../api/client');
      
      await expect(searchListings({})).rejects.toThrow('Erreur 500');
    });
  });

  describe('getPatterns', () => {
    it('makes GET request to /patterns', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValueOnce([]),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { getPatterns } = require('../../api/client');
      await getPatterns();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/patterns'),
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('returns array of patterns', async () => {
      const patterns = [{ id: '1', name: 'Pattern' }];
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValueOnce(patterns),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { getPatterns } = require('../../api/client');
      const result = await getPatterns();
      
      expect(result).toEqual(patterns);
    });
  });

  describe('createPattern', () => {
    it('makes POST request to /patterns', async () => {
      const mockResponse = {
        ok: true,
        status: 201,
        json: jest.fn().mockResolvedValueOnce({ id: '1' }),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { createPattern } = require('../../api/client');
      const data = { name: 'Test' };
      await createPattern(data);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/patterns'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('deletePattern', () => {
    it('makes DELETE request to /patterns/:id', async () => {
      const mockResponse = {
        ok: true,
        status: 204,
        json: jest.fn().mockResolvedValueOnce(null),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { deletePattern } = require('../../api/client');
      await deletePattern('123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/patterns/123'),
        expect.objectContaining({ method: 'DELETE' })
      );
    });

    it('returns null for 204 response', async () => {
      const mockResponse = {
        ok: true,
        status: 204,
        json: jest.fn(),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { deletePattern } = require('../../api/client');
      const result = await deletePattern('123');
      
      expect(result).toBeNull();
    });
  });

  describe('getVehicle', () => {
    it('makes GET request with query parameters', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValueOnce({}),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { getVehicle } = require('../../api/client');
      await getVehicle('Renault', 'Clio');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/vehicles?brand=Renault&model=Clio'),
        expect.anything()
      );
    });

    it('encodes special characters in parameters', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValueOnce({}),
      };
      global.fetch.mockResolvedValueOnce(mockResponse);

      const { getVehicle } = require('../../api/client');
      await getVehicle('Peugeot-Citroën', 'C3 Picasso');

      const url = global.fetch.mock.calls[0][0];
      expect(url).toContain(encodeURIComponent('Peugeot-Citroën'));
      expect(url).toContain(encodeURIComponent('C3 Picasso'));
    });
  });
});
