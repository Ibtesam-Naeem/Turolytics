import { useCallback, useRef } from "react";
import { bouncieService } from "@/services/bouncie-service";
import { useToast } from "@/hooks/use-toast";

/**
 * Hook to automatically re-authenticate Bouncie when tokens expire
 * Opens OAuth flow in a popup window for seamless re-authentication
 */
export const useBouncieAutoReauth = () => {
  const { toast } = useToast();
  const reauthInProgressRef = useRef(false);
  const popupRef = useRef<Window | null>(null);

  /**
   * Check if error indicates token expiration
   */
  const isTokenExpiredError = (error: any): boolean => {
    if (!error) return false;
    const errorMessage = error.message || error.toString() || "";
    return (
      errorMessage.includes("Token expired") ||
      errorMessage.includes("refresh token") ||
      errorMessage.includes("Please reconnect Bouncie") ||
      errorMessage.includes("401") ||
      errorMessage.includes("No refresh token")
    );
  };

  /**
   * Automatically trigger OAuth re-authentication using popup window
   */
  const triggerAutoReauth = useCallback(async (): Promise<boolean> => {
    // Prevent multiple simultaneous re-auth attempts
    if (reauthInProgressRef.current) {
      console.log("[Bouncie Auto Reauth] Re-authentication already in progress");
      return false;
    }

    // Close any existing popup
    if (popupRef.current && !popupRef.current.closed) {
      popupRef.current.close();
    }

    try {
      reauthInProgressRef.current = true;
      console.log("[Bouncie Auto Reauth] Starting automatic re-authentication...");

      // Get authorization URL
      const authUrl = await bouncieService.getAuthorizationUrl();

      // Open OAuth in popup window
      const width = 600;
      const height = 700;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;

      popupRef.current = window.open(
        authUrl,
        "Bouncie Authentication",
        `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no,scrollbars=yes,resizable=yes`
      );

      if (!popupRef.current) {
        throw new Error("Failed to open popup window. Please allow popups for this site.");
      }

      // Show toast notification
      toast({
        title: "Re-authenticating Bouncie",
        description: "Please complete authentication in the popup window.",
      });

      // Listen for message from popup (if backend sends postMessage)
      // Also poll popup closed state and check connection status
      return new Promise((resolve) => {
        let resolved = false;
        
        // Listen for postMessage from popup (if implemented)
        const messageHandler = (event: MessageEvent) => {
          if (event.data?.type === 'BOUNCIE_REAUTH_SUCCESS' || event.data?.bouncie_success) {
            if (!resolved) {
              resolved = true;
              window.removeEventListener('message', messageHandler);
              if (popupRef.current && !popupRef.current.closed) {
                popupRef.current.close();
              }
              reauthInProgressRef.current = false;
              
              setTimeout(async () => {
                try {
                  const status = await bouncieService.getIntegrationStatus();
                  if (status.connected && !status.expired) {
                    toast({
                      title: "Re-authentication Successful",
                      description: "Bouncie connection has been restored.",
                    });
                    resolve(true);
                  } else {
                    resolve(false);
                  }
                } catch (err) {
                  resolve(false);
                }
              }, 1000);
            }
          }
        };
        window.addEventListener('message', messageHandler);

        // Poll popup closed state and check connection status
        const checkPopup = setInterval(async () => {
          if (!popupRef.current || popupRef.current.closed) {
            if (!resolved) {
              resolved = true;
              clearInterval(checkPopup);
              window.removeEventListener('message', messageHandler);
              reauthInProgressRef.current = false;
              
              // Wait a moment for backend to process callback
              await new Promise(resolve => setTimeout(resolve, 2000));
              
              // Check if re-auth was successful
              try {
                const status = await bouncieService.getIntegrationStatus();
                if (status.connected && !status.expired) {
                  toast({
                    title: "Re-authentication Successful",
                    description: "Bouncie connection has been restored.",
                  });
                  resolve(true);
                } else {
                  toast({
                    title: "Re-authentication Failed",
                    description: "Please try connecting again in Settings.",
                    variant: "destructive",
                  });
                  resolve(false);
                }
              } catch (err) {
                toast({
                  title: "Re-authentication Failed",
                  description: "Please try connecting again in Settings.",
                  variant: "destructive",
                });
                resolve(false);
              }
            }
            return;
          }
        }, 500);

        // Timeout after 5 minutes
        setTimeout(() => {
          if (!resolved) {
            resolved = true;
            clearInterval(checkPopup);
            window.removeEventListener('message', messageHandler);
            if (popupRef.current && !popupRef.current.closed) {
              popupRef.current.close();
            }
            reauthInProgressRef.current = false;
            toast({
              title: "Re-authentication Timeout",
              description: "Please try connecting again in Settings.",
              variant: "destructive",
            });
            resolve(false);
          }
        }, 5 * 60 * 1000);
      });
    } catch (error) {
      reauthInProgressRef.current = false;
      console.error("[Bouncie Auto Reauth] Failed to trigger re-authentication:", error);
      toast({
        title: "Re-authentication Failed",
        description: error instanceof Error ? error.message : "Please try connecting again in Settings.",
        variant: "destructive",
      });
      return false;
    }
  }, [toast]);

  /**
   * Handle error and automatically re-authenticate if token expired
   */
  const handleErrorWithAutoReauth = useCallback(
    async (error: any): Promise<boolean> => {
      if (isTokenExpiredError(error)) {
        console.log("[Bouncie Auto Reauth] Token expired error detected, triggering auto re-auth");
        return await triggerAutoReauth();
      }
      return false;
    },
    [triggerAutoReauth]
  );

  return {
    triggerAutoReauth,
    handleErrorWithAutoReauth,
    isTokenExpiredError,
  };
};

