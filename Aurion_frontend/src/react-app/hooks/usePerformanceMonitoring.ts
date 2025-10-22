import { useRef } from 'react';

interface PerformanceMetrics {
  responseTime: number;
  successRate: number;
  errorCount: number;
  totalRequests: number;
}

export const usePerformanceMonitoring = () => {
  const metricsRef = useRef<PerformanceMetrics>({
    responseTime: 0,
    successRate: 100,
    errorCount: 0,
    totalRequests: 0
  });
  
  const trackRequest = (startTime: number, success: boolean) => {
    const responseTime = Date.now() - startTime;
    metricsRef.current.responseTime = responseTime;
    metricsRef.current.totalRequests++;
    
    if (!success) {
      metricsRef.current.errorCount++;
    }
    
    // Calculate success rate
    metricsRef.current.successRate = 
      ((metricsRef.current.totalRequests - metricsRef.current.errorCount) / 
       metricsRef.current.totalRequests) * 100;
    
    // Send to analytics if available
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'mini_agent_request', {
        response_time: responseTime,
        success: success,
        success_rate: metricsRef.current.successRate
      });
    }
    
    // Log performance warnings
    if (responseTime > 3000) {
      console.warn(`Slow Mini Agent response: ${responseTime}ms`);
    }
  };
  
  const getMetrics = () => metricsRef.current;
  
  const resetMetrics = () => {
    metricsRef.current = {
      responseTime: 0,
      successRate: 100,
      errorCount: 0,
      totalRequests: 0
    };
  };
  
  return { trackRequest, getMetrics, resetMetrics };
};
