import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import ExamForm from "@/components/ExamForm";
import SignOutButton from "@/components/SignOutButton";

export default async function Home() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <main className="flex min-h-screen flex-col items-center gap-8 p-8">
      <div className="flex w-full max-w-2xl items-center justify-between">
        <h1 className="text-2xl font-semibold">Banderitasrob</h1>
        <SignOutButton />
      </div>
      <ExamForm />
    </main>
  );
}
