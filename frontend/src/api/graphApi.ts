import api from '@/api';
import type { GraphResponse } from '@/types/graph';

const graphApi = {
  async fetchGraph(): Promise<GraphResponse> {
    const { data } = await api.get<GraphResponse>('/graph');
    return data;
  },
};

export default graphApi;

