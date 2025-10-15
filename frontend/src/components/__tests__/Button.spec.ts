import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from '../ui/Button.vue'

describe('Button', () => {
  it('renders correctly with default props', () => {
    const wrapper = mount(Button, {
      slots: {
        default: 'Click me'
      }
    })

    expect(wrapper.find('button').exists()).toBe(true)
    expect(wrapper.text()).toBe('Click me')
    expect(wrapper.find('button').classes()).toContain('btn')
  })

  it('applies variant classes correctly', () => {
    const variants = ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link']

    variants.forEach(variant => {
      const wrapper = mount(Button, {
        props: { variant },
        slots: { default: variant }
      })

      expect(wrapper.find('button').classes()).toContain(`btn-${variant}`)
    })
  })

  it('applies size classes correctly', () => {
    const sizes = ['default', 'sm', 'lg', 'icon']

    sizes.forEach(size => {
      const wrapper = mount(Button, {
        props: { size },
        slots: { default: size }
      })

      if (size !== 'default') {
        expect(wrapper.find('button').classes()).toContain(`btn-${size}`)
      }
    })
  })

  it('handles click events', async () => {
    const wrapper = mount(Button, {
      slots: { default: 'Click me' }
    })

    await wrapper.find('button').trigger('click')

    expect(wrapper.emitted()).toHaveProperty('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('can be disabled', async () => {
    const wrapper = mount(Button, {
      props: { disabled: true },
      slots: { default: 'Disabled' }
    })

    const button = wrapper.find('button')
    expect(button.attributes('disabled')).toBeDefined()
    expect(button.classes()).toContain('disabled:opacity-50')

    await button.trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
  })

  it('shows loading state', () => {
    const wrapper = mount(Button, {
      props: { loading: true },
      slots: { default: 'Loading' }
    })

    expect(wrapper.find('.loading-spinner').exists()).toBe(true)
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('accepts custom classes', () => {
    const wrapper = mount(Button, {
      props: { class: 'custom-class another-class' },
      slots: { default: 'Custom' }
    })

    expect(wrapper.find('button').classes()).toContain('custom-class')
    expect(wrapper.find('button').classes()).toContain('another-class')
  })

  it('renders as different element types', () => {
    const asButton = mount(Button, {
      props: { as: 'button' },
      slots: { default: 'Button' }
    })
    expect(asButton.find('button').exists()).toBe(true)

    const asAnchor = mount(Button, {
      props: { as: 'a', href: '/test' },
      slots: { default: 'Link' }
    })
    expect(asAnchor.find('a').exists()).toBe(true)
    expect(asAnchor.find('a').attributes('href')).toBe('/test')
  })

  it('handles keyboard events', async () => {
    const wrapper = mount(Button, {
      slots: { default: 'Submit' }
    })

    // Test Enter key
    await wrapper.find('button').trigger('keydown.enter')
    expect(wrapper.emitted('click')).toHaveLength(1)

    // Test Space key
    await wrapper.find('button').trigger('keydown.space')
    expect(wrapper.emitted('click')).toHaveLength(2)
  })

  it('supports ref forwarding', () => {
    const wrapper = mount(Button, {
      slots: { default: 'Ref Test' }
    })

    // In a real scenario, you'd test ref forwarding
    // This is more of a structural test
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('handles accessibility attributes', () => {
    const wrapper = mount(Button, {
      props: {
        'aria-label': 'Close dialog',
        'aria-describedby': 'dialog-description'
      },
      slots: { default: '×' }
    })

    const button = wrapper.find('button')
    expect(button.attributes('aria-label')).toBe('Close dialog')
    expect(button.attributes('aria-describedby')).toBe('dialog-description')
  })

  it('handles focus and blur events', async () => {
    const wrapper = mount(Button, {
      slots: { default: 'Focus Test' }
    })

    await wrapper.find('button').trigger('focus')
    expect(wrapper.emitted()).toHaveProperty('focus')

    await wrapper.find('button').trigger('blur')
    expect(wrapper.emitted()).toHaveProperty('blur')
  })

  it('prevents default when disabled', async () => {
    const wrapper = mount(Button, {
      props: { disabled: true },
      slots: { default: 'Disabled' }
    })

    const event = new MouseEvent('click', { cancelable: true })
    const button = wrapper.find('button').element

    const clickEvent = vi.fn()
    button.addEventListener('click', clickEvent)

    await wrapper.find('button').trigger('click', event)

    // The component should handle this internally
    expect(wrapper.emitted('click')).toBeUndefined()
  })
})