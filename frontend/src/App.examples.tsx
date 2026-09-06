import React from 'react';
import { Button, Input } from '../components/ui';

/**
 * Example Usage of Professional UI Components
 * 
 * This demonstrates how to compose components together
 * following the core principles: Composable, Reusable, Accessible, Customizable.
 */
const ComponentExamples: React.FC = () => {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-12">
      
      {/* Section: Buttons */}
      <section>
        <h2 className="text-xl font-semibold mb-4 text-[var(--color-neutral-900)]">
          Button Variants
        </h2>
        <div className="flex flex-wrap gap-4 items-center">
          <Button variant="primary">Primary Action</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Delete</Button>
        </div>

        <h3 className="text-lg font-medium mt-6 mb-3 text-[var(--color-neutral-800)]">
          Button Sizes
        </h3>
        <div className="flex flex-wrap gap-4 items-center">
          <Button size="sm" variant="primary">Small</Button>
          <Button size="md" variant="primary">Medium</Button>
          <Button size="lg" variant="primary">Large</Button>
        </div>

        <h3 className="text-lg font-medium mt-6 mb-3 text-[var(--color-neutral-800)]">
          Loading & Disabled States
        </h3>
        <div className="flex flex-wrap gap-4 items-center">
          <Button isLoading variant="primary">Loading...</Button>
          <Button disabled variant="primary">Disabled</Button>
          <Button 
            variant="outline" 
            leftIcon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            }
          >
            Upload
          </Button>
        </div>
      </section>

      <hr className="border-[var(--color-neutral-200)]" />

      {/* Section: Inputs */}
      <section>
        <h2 className="text-xl font-semibold mb-4 text-[var(--color-neutral-900)]">
          Input Fields
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Default Input */}
          <Input 
            label="Email Address" 
            placeholder="you@example.com" 
            type="email"
          />

          {/* Input with Helper Text */}
          <Input 
            label="Username" 
            placeholder="johndoe"
            helperText="Choose a unique username for your profile."
          />

          {/* Input with Error State */}
          <Input 
            label="Password" 
            type="password"
            defaultValue="incorrect"
            variant="error"
            error="Password must be at least 8 characters."
          />

          {/* Input with Success State */}
          <Input 
            label="Confirm Password" 
            type="password"
            defaultValue="correctpassword123"
            variant="success"
          />

          {/* Input with Left Element (Icon) */}
          <Input 
            label="Search" 
            placeholder="Search products..."
            leftElement={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            }
          />

          {/* Input with Right Element */}
          <Input 
            label="Website" 
            placeholder="example.com"
            rightElement={
              <span className="text-xs text-[var(--color-neutral-500)]">https://</span>
            }
          />

          {/* Disabled Input */}
          <Input 
            label="Disabled Field" 
            defaultValue="Cannot edit this"
            disabled
          />

          {/* Small & Large Sizes */}
          <div className="space-y-4">
            <Input size="sm" label="Small Input" placeholder="Compact size" />
            <Input size="lg" label="Large Input" placeholder="Comfortable size" />
          </div>
        </div>
      </section>

      <hr className="border-[var(--color-neutral-200)]" />

      {/* Section: Composed Form Example */}
      <section>
        <h2 className="text-xl font-semibold mb-4 text-[var(--color-neutral-900)]">
          Composed Form Example
        </h2>
        <div className="max-w-md space-y-4 p-6 rounded-lg bg-[var(--color-neutral-50)] border border-[var(--color-neutral-200)]">
          <Input 
            label="Full Name" 
            placeholder="John Doe"
            autoComplete="name"
          />
          <Input 
            label="Email" 
            type="email"
            placeholder="john@example.com"
            autoComplete="email"
          />
          <div className="flex gap-3 pt-2">
            <Button variant="outline" className="flex-1">Cancel</Button>
            <Button variant="primary" className="flex-1">Submit</Button>
          </div>
        </div>
      </section>

    </div>
  );
};

export default ComponentExamples;
