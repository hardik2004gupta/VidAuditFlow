"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { CopilotPanel } from "@/features/reports/components/copilot/copilot-panel";
import { useMediaQuery } from "@/hooks/use-media-query";

/**
 * Entry point for the report's AI Copilot: a floating action button that
 * opens the same `CopilotPanel` in different chrome depending on viewport
 * -- a non-modal ~360px right sidebar on desktop (so the report stays
 * usable behind it), a modal bottom sheet on mobile (UI_VISION.md's
 * existing convention for the chat panel on small screens). Purely
 * additive to the report page: nothing else on the page moves or resizes
 * when this opens.
 */
export function CopilotLauncher({ reportId }: { reportId: string }) {
  const [open, setOpen] = useState(false);
  const isDesktop = useMediaQuery("(min-width: 1024px)");

  useEffect(() => {
    if (!open || !isDesktop) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, isDesktop]);

  return (
    <>
      <AnimatePresence>
        {!open && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed right-6 bottom-6 z-40"
          >
            <Button
              size="icon-lg"
              className="size-12 rounded-full shadow-lg"
              aria-label="Open AI Copilot"
              onClick={() => setOpen(true)}
            >
              <MessageCircle className="size-5" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {isDesktop ? (
        <AnimatePresence>
          {open && (
            <motion.aside
              initial={{ x: 360, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 360, opacity: 0 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className="fixed top-16 right-0 bottom-0 z-40 w-[360px] border-l border-border shadow-xl"
              role="complementary"
              aria-label="AI Copilot"
            >
              <CopilotPanel reportId={reportId} onClose={() => setOpen(false)} />
            </motion.aside>
          )}
        </AnimatePresence>
      ) : (
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent side="bottom" showCloseButton={false} className="h-[80vh] gap-0 border-t p-0">
            <SheetTitle className="sr-only">AI Copilot</SheetTitle>
            <CopilotPanel reportId={reportId} onClose={() => setOpen(false)} />
          </SheetContent>
        </Sheet>
      )}
    </>
  );
}
