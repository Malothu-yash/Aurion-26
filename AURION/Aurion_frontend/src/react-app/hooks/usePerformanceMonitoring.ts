import { useEffect, useRef } from 'react';

interface PerformanceMetrics {
  responseTime: number;
  successRate: number;
  errorCount: number;
}

export const usePerformanceMonitoring = () => {
  const metricsRef = useRef<PerformanceMetrics>({
    responseTime: 0,
    successRate: 100,
    errorCount: 0
  });
  
  const trackRequest = (startTime: number, success: boolean) => {
    const responseTime = Date.now() - startTime;
    metricsRef.current.responseTime = responseTime;
    
    if (!success) {
      metricsRef.current.errorCount++;
    }
    
    // Send to analytics
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'mini_agent_request', {
        response_time: responseTime,
        success: success
      });
    }
  };
  
  const getMetrics = () => metricsRef.current;
  
  return { trackRequest, getMetrics };
};