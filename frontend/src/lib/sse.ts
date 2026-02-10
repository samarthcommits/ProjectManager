export interface SSEEvent {
  type: 'status' | 'result' | 'error';
  msg?: string;
  data?: unknown;
}

export async function consumeSSE(
  url: string,
  body: unknown,
  onEvent: (event: SSEEvent) => void,
  onError: (error: Error) => void,
  onComplete: () => void,
  signal?: AbortSignal,
) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(':')) continue;
        if (trimmed.startsWith('data: ')) {
          const jsonStr = trimmed.slice(6);
          if (jsonStr === '[DONE]') {
            onComplete();
            return;
          }
          try {
            const event = JSON.parse(jsonStr) as SSEEvent;
            onEvent(event);
          } catch {
            // Incomplete JSON chunk, skip
          }
        }
      }
    }
    onComplete();
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') return;
    onError(error instanceof Error ? error : new Error('Unknown error'));
  }
}
