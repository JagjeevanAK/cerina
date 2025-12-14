"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import type { CreateSessionRequest, Session } from "@/types/session";

interface CreateSessionDialogProps {
  trigger: React.ReactNode;
  onSubmit: (request: CreateSessionRequest) => Promise<Session>;
  onSuccess?: (session: Session) => void;
}

export function CreateSessionDialog({
  trigger,
  onSubmit,
  onSuccess,
}: CreateSessionDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [userInput, setUserInput] = useState("");
  const [exerciseTypeHint, setExerciseTypeHint] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!userInput.trim() || userInput.length < 10) {
      setError("Please enter at least 10 characters");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    // Store values before clearing
    const requestData = {
      user_input: userInput,
      exercise_type_hint: exerciseTypeHint || undefined,
    };

    // Reset form
    setUserInput("");
    setExerciseTypeHint("");

    try {
      // Start the session creation - this will wait for backend
      const session = await onSubmit(requestData);
      
      // Close dialog
      setOpen(false);
      
      // Navigate to the new session to show live progress
      if (session?.session_id) {
        router.push(`/sessions/${session.session_id}`);
      }
      
      onSuccess?.(session);
    } catch (err) {
      console.error("Failed to create session:", err);
      // Show error in dialog
      setError(err instanceof Error ? err.message : "Failed to create session");
      // Restore form values
      setUserInput(requestData.user_input);
      setExerciseTypeHint(requestData.exercise_type_hint || "");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create CBT Exercise</DialogTitle>
          <DialogDescription>
            Describe the CBT exercise you want to create. The multi-agent system
            will draft, review, and refine it.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label htmlFor="user-input" className="text-sm font-medium">
              Exercise Description
            </label>
            <Textarea
              id="user-input"
              placeholder="E.g., Create an exposure hierarchy for agoraphobia with 10 steps ranging from mild to severe anxiety triggers..."
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              rows={4}
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground">
              {userInput.length}/2000 characters (minimum 10)
            </p>
          </div>

          <div className="space-y-2">
            <label htmlFor="type-hint" className="text-sm font-medium">
              Exercise Type Hint (optional)
            </label>
            <Input
              id="type-hint"
              placeholder="E.g., exposure_hierarchy, thought_record, behavioral_activation"
              value={exerciseTypeHint}
              onChange={(e) => setExerciseTypeHint(e.target.value)}
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isSubmitting ? "Creating..." : "Create Exercise"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
