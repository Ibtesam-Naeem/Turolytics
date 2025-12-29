import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * Bouncie OAuth callback page
 * This page handles the OAuth callback and closes the popup window,
 * sending a message to the parent window if opened in a popup
 */
const BouncieCallback = () => {
  const [searchParams] = useSearchParams();
  const success = searchParams.get("success") === "true";
  const error = searchParams.get("error");
  // Detect if opened in popup (check window.opener - most reliable)
  const isPopup = typeof window !== "undefined" && window.opener !== null;

  useEffect(() => {
    // If opened in a popup, send message to parent and close
    if (isPopup && window.opener) {
      if (success) {
        window.opener.postMessage(
          { type: "BOUNCIE_REAUTH_SUCCESS", success: true },
          window.location.origin
        );
      } else if (error) {
        window.opener.postMessage(
          { type: "BOUNCIE_REAUTH_ERROR", error },
          window.location.origin
        );
      }
      
      // Close popup after a short delay
      setTimeout(() => {
        window.close();
      }, 500);
    } else {
      // If not a popup, redirect to settings
      if (success) {
        window.location.href = "/settings?bouncie_success=true";
      } else {
        window.location.href = `/settings?bouncie_error=${error || "unknown_error"}`;
      }
    }
  }, [success, error, isPopup]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        {success ? (
          <>
            <h1 className="text-2xl font-bold mb-2">Authentication Successful!</h1>
            <p className="text-muted-foreground">Closing window...</p>
          </>
        ) : (
          <>
            <h1 className="text-2xl font-bold mb-2 text-destructive">Authentication Failed</h1>
            <p className="text-muted-foreground">Closing window...</p>
          </>
        )}
      </div>
    </div>
  );
};

export default BouncieCallback;

