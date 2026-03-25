/**
 * Хук для загрузки макро данных с ЦБ РФ
 * Использует money.js и cbr-xml-daily.ru
 */

import { useState, useEffect } from 'react';

interface MacroData {
  key_rate: number;
  usd_rub: number;
  eur_rub: number;
  oil_price: number;
  inflation: number;
  loaded: boolean;
  error: string | null;
}

const DEFAULT_MACRO: MacroData = {
  key_rate: 18.0,
  usd_rub: 90.0,
  eur_rub: 98.0,
  oil_price: 85.0,
  inflation: 7.5,
  loaded: false,
  error: null,
};

export function useMacroData() {
  const [macro, setMacro] = useState<MacroData>(DEFAULT_MACRO);

  useEffect(() => {
    loadMacroData();
  }, []);

  const loadMacroData = async () => {
    try {
      // 1. Загружаем money.js динамически
      if (!(window as any).fx) {
        await loadScript('https://www.cbr-xml-daily.ru/money.js');
      }

      // 2. Получаем данные с API ЦБ
      const response = await fetch('https://www.cbr-xml-daily.ru/dynamic_json');
      const data = await response.json();

      // 3. Используем money.js для конвертации (если нужно)
      const fx = (window as any).fx;

      setMacro({
        key_rate: data.key_rate || DEFAULT_MACRO.key_rate,
        usd_rub: data.USD || DEFAULT_MACRO.usd_rub,
        eur_rub: data.EUR || DEFAULT_MACRO.eur_rub,
        oil_price: DEFAULT_MACRO.oil_price, // Нефть не в API ЦБ
        inflation: DEFAULT_MACRO.inflation,  // Инфляция отдельно
        loaded: true,
        error: null,
      });
    } catch (error) {
      console.error('Ошибка загрузки макро данных:', error);
      setMacro({
        ...DEFAULT_MACRO,
        error: 'Не удалось загрузить макро данные. Используем значения по умолчанию.',
      });
    }
  };

  return macro;
}

// Функция для динамической загрузки скрипта
function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
    document.head.appendChild(script);
  });
}

// Хук для получения актуальных данных по тикеру
export function useCurrentMacro(ticker?: string) {
  const macro = useMacroData();

  const getMacroForTicker = () => {
    if (!ticker) return null;

    return {
      ticker,
      ...macro,
      timestamp: new Date().toISOString(),
    };
  };

  return {
    ...macro,
    getMacroForTicker,
  };
}
