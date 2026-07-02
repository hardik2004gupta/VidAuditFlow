import { HeroSection } from "@/features/landing/components/hero-section";
import { FeaturesSection } from "@/features/landing/components/features-section";
import { ArchitectureSection } from "@/features/landing/components/architecture-section";
import { TechStackSection } from "@/features/landing/components/tech-stack-section";
import { CtaSection } from "@/features/landing/components/cta-section";

export default function LandingPage() {
  return (
    <>
      <HeroSection />
      <FeaturesSection />
      <ArchitectureSection />
      <TechStackSection />
      <CtaSection />
    </>
  );
}
